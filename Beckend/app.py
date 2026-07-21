"""Backend de ManabIA.

ManabIA es un tutor educativo con IA para contextos con conectividad
intermitente. El servidor usa OpenAI cuando la clave y el SDK están
disponibles y degrada automáticamente a respuestas simuladas cuando no lo
están o cuando una llamada externa falla.

El estado de la demo se conserva únicamente en memoria. No requiere una base
de datos ni autenticación.
"""

import base64
import copy
import html
import json
import os
import threading
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

try:
    from openai import OpenAI
except Exception:  # El modo simulado también debe funcionar sin el SDK.
    OpenAI = None


PROJECT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_DIR / "Fronted"
CHAT_DIR = FRONTEND_DIR / "Chat"
PANEL_DIR = FRONTEND_DIR / "Panel"
ASSETS_DIR = FRONTEND_DIR / "assets"

TEXT_MODEL = os.environ.get(
    "OPENAI_MODEL", os.environ.get("OPENAI_TEXT_MODEL", "gpt-4o-mini")
)
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-1-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

app = Flask(__name__, static_folder=None)
app.config["JSON_AS_ASCII"] = False


def _crear_cliente_openai():
    if not OPENAI_API_KEY:
        return None, "Modo simulado activo: no se configuró OPENAI_API_KEY."
    if OpenAI is None:
        return None, "Modo simulado activo: el módulo openai no está instalado."

    try:
        return (
            OpenAI(
                api_key=OPENAI_API_KEY,
                timeout=15.0,
                max_retries=0,
            ),
            None,
        )
    except Exception as exc:
        app.logger.warning(
            "No se pudo inicializar OpenAI; se usará simulación (%s).",
            type(exc).__name__,
        )
        return None, "Modo simulado activo: no se pudo inicializar OpenAI."


OPENAI_CLIENT, OPENAI_STARTUP_NOTICE = _crear_cliente_openai()

# Estado en memoria para la demo.
STATE_LOCK = threading.RLock()
historial = {}
escalados = []
claves_escaladas = set()
contadores_preguntas = {}
resultados_por_intento = {}
intentos_en_curso = {}


def _respuesta_error(detalle, status=400):
    return jsonify({"error": "Solicitud inválida", "detalle": detalle}), status


def _leer_json():
    if not request.is_json:
        return None, _respuesta_error(
            "El cuerpo debe enviarse como JSON con Content-Type application/json."
        )

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, _respuesta_error("El cuerpo JSON debe ser un objeto.")
    return data, None


def _leer_texto(data, nombre, requerido=False, maximo=4000, por_defecto=""):
    if nombre not in data:
        if requerido:
            return None, f"El campo '{nombre}' es obligatorio."
        return por_defecto, None

    valor = data.get(nombre)
    if valor is None and not requerido:
        return por_defecto, None
    if not isinstance(valor, str):
        return None, f"El campo '{nombre}' debe ser texto."

    valor = valor.strip()
    if requerido and not valor:
        return None, f"El campo '{nombre}' no puede estar vacío."
    if len(valor) > maximo:
        return None, f"El campo '{nombre}' no puede superar {maximo} caracteres."
    return valor, None


def _payload_con_modo(payload, modo, aviso=None):
    respuesta = dict(payload)
    respuesta["modo"] = modo
    if aviso:
        respuesta["aviso"] = aviso
    return respuesta


def _con_modo(payload, modo, aviso=None):
    return jsonify(_payload_con_modo(payload, modo, aviso))


def _aviso_fallo_openai(exc):
    nombre = type(exc).__name__.lower()
    app.logger.warning(
        "OpenAI falló; la solicitud continuará en modo simulado (%s).",
        type(exc).__name__,
    )
    if "timeout" in nombre:
        return "OpenAI tardó demasiado; se usó el modo simulado para continuar."
    return "OpenAI no estuvo disponible; se usó el modo simulado para continuar."


def _normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.casefold())
    return "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")


def _clave_estado(estudiante, tema):
    estudiante_normalizado = " ".join(_normalizar(estudiante).split())
    tema_normalizado = " ".join(_normalizar(tema).split())
    return estudiante_normalizado, tema_normalizado


def _contenido_mensaje(message):
    contenido = getattr(message, "content", None)
    if isinstance(contenido, str):
        return contenido
    if isinstance(contenido, list):
        partes = []
        for parte in contenido:
            if isinstance(parte, dict) and isinstance(parte.get("text"), str):
                partes.append(parte["text"])
            elif isinstance(getattr(parte, "text", None), str):
                partes.append(parte.text)
        return "".join(partes)
    raise ValueError("OpenAI no devolvió contenido de texto.")


def _explicacion_simulada(tema, texto=""):
    tema_normalizado = _normalizar(tema)
    ejemplos = (
        (
            "fraccion",
            "Una fracción representa una o varias partes iguales de un todo. "
            "El número de arriba indica cuántas partes tomamos y el de abajo "
            "en cuántas partes iguales se dividió el todo. Por ejemplo, 1/4 es "
            "una de cuatro partes iguales.",
            "Si una torta se divide en 4 partes iguales, ¿qué representa 1/4?",
        ),
        (
            "fotosintesis",
            "La fotosíntesis es el proceso con el que las plantas producen su "
            "alimento. Usan luz solar, agua y dióxido de carbono; además liberan "
            "oxígeno. Las hojas funcionan como pequeños talleres que aprovechan "
            "la energía del sol.",
            "¿Qué tres elementos necesita una planta para realizar la fotosíntesis?",
        ),
        (
            "verbo",
            "Los verbos en pasado cuentan acciones que ya ocurrieron. En español "
            "podemos decir 'ayer caminé' o 'la semana pasada estudiamos'. Las "
            "palabras de tiempo ayudan a reconocer cuándo sucedió la acción.",
            "En la oración 'Ayer María sembró maíz', ¿cuál es el verbo en pasado?",
        ),
        (
            "ciclo del agua",
            "El agua cambia de lugar y de estado continuamente. El sol causa la "
            "evaporación, el vapor forma nubes por condensación y luego el agua "
            "regresa como precipitación. Después se acumula y el ciclo comienza otra vez.",
            "¿Qué etapa del ciclo del agua forma las nubes?",
        ),
    )

    if texto:
        resumen = " ".join(texto.split())
        if len(resumen) > 420:
            resumen = resumen[:417].rstrip() + "..."
        explicacion = (
            f"Para estudiar {tema}, partamos del material compartido: “{resumen}” "
            "La idea clave se entiende mejor si identificas qué ocurre, por qué "
            "ocurre y lo relacionas con un ejemplo cercano."
        )
        pregunta = f"Según el texto, ¿cuál es la idea principal sobre {tema}?"
        return explicacion, pregunta

    for palabra, explicacion, pregunta in ejemplos:
        if palabra in tema_normalizado:
            return explicacion, pregunta

    explicacion = (
        f"Para comprender {tema}, empieza por identificar su idea principal, "
        "después relaciónala con una situación de tu vida diaria y finalmente "
        "explícala con tus propias palabras. Ese proceso permite detectar qué "
        "parte ya dominas y cuál necesitas repasar."
    )
    pregunta = f"Con tus propias palabras, ¿qué entendiste sobre {tema} y qué ejemplo darías?"
    return explicacion, pregunta


def _explicacion_real(tema, texto):
    material = texto or "No se proporcionó un texto base."
    response = OPENAI_CLIENT.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres ManabIA, un tutor educativo para estudiantes de Manabí, "
                    "Ecuador. Explica con lenguaje sencillo, respetuoso y cercano, "
                    "sin inventar datos. Devuelve una explicación breve y una sola "
                    "pregunta clara para verificar comprensión."
                ),
            },
            {
                "role": "user",
                "content": f"Tema: {tema}\nTexto base opcional:\n{material}",
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "explicacion_manabia",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "explicacion": {"type": "string"},
                        "pregunta": {"type": "string"},
                    },
                    "required": ["explicacion", "pregunta"],
                    "additionalProperties": False,
                },
            },
        },
    )
    contenido = _contenido_mensaje(response.choices[0].message)
    resultado = json.loads(contenido)
    explicacion = resultado.get("explicacion")
    pregunta = resultado.get("pregunta")
    if not isinstance(explicacion, str) or not explicacion.strip():
        raise ValueError("La explicación de OpenAI no es válida.")
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("La pregunta de OpenAI no es válida.")
    return explicacion.strip(), pregunta.strip()


PALABRAS_COMUNES = {
    "a",
    "al",
    "ante",
    "como",
    "con",
    "cual",
    "de",
    "del",
    "el",
    "en",
    "es",
    "esta",
    "la",
    "las",
    "lo",
    "los",
    "para",
    "por",
    "que",
    "se",
    "si",
    "su",
    "un",
    "una",
    "y",
}


def _palabras_relevantes(texto):
    limpio = "".join(
        caracter if caracter.isalnum() or caracter.isspace() else " "
        for caracter in _normalizar(texto)
    )
    return [
        palabra
        for palabra in limpio.split()
        if len(palabra) > 1 and palabra not in PALABRAS_COMUNES
    ]


def _evaluacion_simulada(tema, pregunta, respuesta):
    normalizada = " ".join(_normalizar(respuesta).split())
    expresiones_rojas = (
        "no se",
        "no entiendo",
        "ni idea",
        "no puedo",
        "no recuerdo",
        "nose",
    )
    if any(expresion in normalizada for expresion in expresiones_rojas):
        return "rojo", "La respuesta indica que el concepto todavía no está claro."

    palabras_respuesta = _palabras_relevantes(respuesta)
    palabras_contexto = set(_palabras_relevantes(f"{tema} {pregunta}"))
    coincidencias = set(palabras_respuesta) & palabras_contexto

    if len(coincidencias) >= 2 or len(palabras_respuesta) >= 10:
        return (
            "verde",
            "La respuesta explica la idea con suficiente claridad y relación con el tema.",
        )
    if len(palabras_respuesta) >= 4 or coincidencias:
        return (
            "amarillo",
            "La respuesta va por buen camino, pero necesita un poco más de detalle.",
        )
    return (
        "rojo",
        "La respuesta es demasiado breve para demostrar comprensión del concepto.",
    )


def _evaluacion_real(tema, pregunta, respuesta):
    completion = OPENAI_CLIENT.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres el evaluador pedagógico de ManabIA. Evalúa comprensión, "
                    "no estilo ni ortografía. Usa rojo si aún no comprende, amarillo "
                    "si comprende parcialmente y verde si demuestra comprensión. La "
                    "razón debe ser concreta, respetuosa y trazable a la respuesta."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Tema: {tema}\nPregunta: {pregunta}\n"
                    f"Respuesta del estudiante: {respuesta}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "evaluacion_manabia",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "semaforo": {
                            "type": "string",
                            "enum": ["rojo", "amarillo", "verde"],
                        },
                        "razon": {"type": "string"},
                    },
                    "required": ["semaforo", "razon"],
                    "additionalProperties": False,
                },
            },
        },
    )
    contenido = _contenido_mensaje(completion.choices[0].message)
    resultado = json.loads(contenido)
    semaforo = resultado.get("semaforo")
    razon = resultado.get("razon")
    if semaforo not in {"rojo", "amarillo", "verde"}:
        raise ValueError("OpenAI devolvió un semáforo no válido.")
    if not isinstance(razon, str) or not razon.strip():
        raise ValueError("OpenAI devolvió una razón no válida.")
    return semaforo, razon.strip()


def _registrar_evaluacion(estudiante, tema, pregunta, respuesta, semaforo, razon):
    fecha = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    clave = _clave_estado(estudiante, tema)

    with STATE_LOCK:
        registros = historial.setdefault(clave, [])
        intento = len(registros) + 1
        registro = {
            "pregunta": pregunta,
            "respuesta": respuesta,
            "fecha": fecha,
            "intento": intento,
            "semaforo": semaforo,
            "razon": razon,
        }
        registros.append(registro)

        escalado_ahora = False
        ultimos_tres = registros[-3:]
        if (
            clave not in claves_escaladas
            and len(ultimos_tres) == 3
            and all(item["semaforo"] == "rojo" for item in ultimos_tres)
        ):
            caso = {
                "id": str(uuid.uuid4()),
                "estudiante": estudiante,
                "tema": tema,
                "motivo": f"3 respuestas consecutivas en rojo. Última razón: {razon}",
                "pregunta": pregunta,
                "respuesta": respuesta,
                "fecha": fecha,
                "intentos": intento,
                "trazabilidad": copy.deepcopy(registros),
            }
            escalados.append(caso)
            claves_escaladas.add(clave)
            escalado_ahora = True

    return escalado_ahora, intento


PREGUNTAS_SIMULADAS = {
    "fraccion": [
        {
            "pregunta": "¿Cuál fracción representa una de cuatro partes iguales?",
            "opciones": ["1/4", "4/1", "1/2", "4/4"],
            "respuesta_correcta": 0,
            "explicacion": "1/4 significa una parte tomada de cuatro partes iguales.",
        },
        {
            "pregunta": "¿Cuál de estas fracciones equivale a la mitad?",
            "opciones": ["1/3", "2/4", "1/4", "3/4"],
            "respuesta_correcta": 1,
            "explicacion": "2/4 se simplifica a 1/2, que representa la mitad.",
        },
        {
            "pregunta": "Una barra se divide en 8 partes y tomas 3. ¿Qué fracción tomaste?",
            "opciones": ["8/3", "3/8", "5/8", "3/5"],
            "respuesta_correcta": 1,
            "explicacion": "Se tomaron 3 de las 8 partes iguales: 3/8.",
        },
    ],
    "fotosintesis": [
        {
            "pregunta": "¿Qué fuente de energía usan las plantas en la fotosíntesis?",
            "opciones": ["La luz solar", "El viento", "El sonido", "La arena"],
            "respuesta_correcta": 0,
            "explicacion": "La luz solar aporta la energía necesaria para el proceso.",
        },
        {
            "pregunta": "¿Qué gas liberan principalmente las plantas durante la fotosíntesis?",
            "opciones": ["Dióxido de carbono", "Oxígeno", "Nitrógeno", "Vapor de sal"],
            "respuesta_correcta": 1,
            "explicacion": "Durante la fotosíntesis, las plantas liberan oxígeno.",
        },
        {
            "pregunta": "¿En qué parte de la planta ocurre principalmente la fotosíntesis?",
            "opciones": ["En las hojas", "En las flores secas", "En el suelo", "En las semillas guardadas"],
            "respuesta_correcta": 0,
            "explicacion": "Las hojas contienen estructuras que captan la luz solar.",
        },
    ],
    "verbo": [
        {
            "pregunta": "¿Cuál oración expresa una acción en pasado?",
            "opciones": ["Ana estudió ayer.", "Ana estudia ahora.", "Ana estudiará mañana.", "Ana quiere estudiar."],
            "respuesta_correcta": 0,
            "explicacion": "“Estudió” indica una acción que ya ocurrió.",
        },
        {
            "pregunta": "¿Cuál es el verbo en pasado de “caminar” para yo?",
            "opciones": ["Camino", "Caminaré", "Caminé", "Caminando"],
            "respuesta_correcta": 2,
            "explicacion": "“Caminé” expresa que la acción ya fue realizada por quien habla.",
        },
        {
            "pregunta": "En “Ellos cosecharon el lunes”, ¿cuál es el verbo?",
            "opciones": ["Ellos", "Cosecharon", "El", "Lunes"],
            "respuesta_correcta": 1,
            "explicacion": "“Cosecharon” nombra la acción realizada en el pasado.",
        },
    ],
}


def _pregunta_simulada(tema, contexto=""):
    tema_normalizado = _normalizar(tema)
    grupo = None
    for palabra, preguntas in PREGUNTAS_SIMULADAS.items():
        if palabra in tema_normalizado:
            grupo = preguntas
            break

    if grupo is None:
        if contexto:
            grupo = [
                {
                    "pregunta": f"Según el material sobre {tema}, ¿qué ayuda a identificar su idea principal?",
                    "opciones": [
                        "Relacionar las ideas y explicarlas con palabras propias",
                        "Copiar una frase sin leerla",
                        "Ignorar los ejemplos",
                        "Elegir la respuesta más larga al azar",
                    ],
                    "respuesta_correcta": 0,
                    "explicacion": "Relacionar y explicar las ideas demuestra comprensión del material.",
                }
            ]
        else:
            grupo = [
                {
                    "pregunta": f"¿Qué acción demuestra mejor que comprendiste {tema}?",
                    "opciones": [
                        "Explicarlo con tus palabras y dar un ejemplo",
                        "Memorizar el título solamente",
                        "Responder al azar",
                        "Evitar hacer preguntas",
                    ],
                    "respuesta_correcta": 0,
                    "explicacion": "Explicar y aplicar una idea permite comprobar que fue comprendida.",
                },
                {
                    "pregunta": f"Si una parte de {tema} no está clara, ¿qué conviene hacer?",
                    "opciones": [
                        "Identificar la duda y pedir otra explicación",
                        "Ocultar la duda",
                        "Cambiar de respuesta sin pensar",
                        "Abandonar el tema de inmediato",
                    ],
                    "respuesta_correcta": 0,
                    "explicacion": "Identificar la duda permite recibir apoyo específico y seguir aprendiendo.",
                },
            ]

    clave = " ".join(tema_normalizado.split())
    with STATE_LOCK:
        indice = contadores_preguntas.get(clave, 0)
        contadores_preguntas[clave] = indice + 1
    return copy.deepcopy(grupo[indice % len(grupo)])


def _validar_pregunta_generada(resultado):
    if not isinstance(resultado, dict):
        raise ValueError("La pregunta generada no es un objeto.")

    pregunta = resultado.get("pregunta")
    opciones = resultado.get("opciones")
    correcta = resultado.get("respuesta_correcta")
    explicacion = resultado.get("explicacion")
    if not isinstance(pregunta, str) or not pregunta.strip():
        raise ValueError("La pregunta generada está vacía.")
    if (
        not isinstance(opciones, list)
        or len(opciones) != 4
        or any(not isinstance(opcion, str) or not opcion.strip() for opcion in opciones)
    ):
        raise ValueError("La pregunta no contiene cuatro opciones válidas.")
    if len({opcion.strip().casefold() for opcion in opciones}) != 4:
        raise ValueError("Las opciones de la pregunta deben ser diferentes.")
    if isinstance(correcta, bool) or not isinstance(correcta, int) or correcta not in range(4):
        raise ValueError("El índice de la respuesta correcta no es válido.")
    if not isinstance(explicacion, str) or not explicacion.strip():
        raise ValueError("La explicación de la respuesta está vacía.")

    return {
        "pregunta": pregunta.strip(),
        "opciones": [opcion.strip() for opcion in opciones],
        "respuesta_correcta": correcta,
        "explicacion": explicacion.strip(),
    }


def _pregunta_real(tema, contexto, dificultad):
    herramienta = {
        "type": "function",
        "function": {
            "name": "crear_pregunta_practica",
            "description": "Crea una pregunta educativa de opción múltiple para ManabIA.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "pregunta": {"type": "string"},
                    "opciones": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "respuesta_correcta": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 3,
                    },
                    "explicacion": {"type": "string"},
                },
                "required": [
                    "pregunta",
                    "opciones",
                    "respuesta_correcta",
                    "explicacion",
                ],
                "additionalProperties": False,
            },
        },
    }
    completion = OPENAI_CLIENT.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres ManabIA. Genera una pregunta de práctica clara, correcta "
                    "y apropiada para estudiantes. Debe tener exactamente cuatro "
                    "opciones distintas, una sola respuesta correcta y una explicación "
                    "breve. Usa obligatoriamente la herramienta disponible."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Tema: {tema}\nDificultad: {dificultad or 'media'}\n"
                    f"Contexto opcional: {contexto or 'sin contexto adicional'}"
                ),
            },
        ],
        tools=[herramienta],
        tool_choice={
            "type": "function",
            "function": {"name": "crear_pregunta_practica"},
        },
    )
    tool_calls = getattr(completion.choices[0].message, "tool_calls", None)
    if not tool_calls:
        raise ValueError("OpenAI no llamó la herramienta solicitada.")
    argumentos = tool_calls[0].function.arguments
    return _validar_pregunta_generada(json.loads(argumentos))


def _svg_simulado(tema):
    titulo = " ".join(tema.split())
    if len(titulo) > 58:
        titulo = titulo[:55].rstrip() + "..."
    titulo = html.escape(titulo)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
  <defs>
    <linearGradient id="fondo" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#e9f8ef"/>
      <stop offset="1" stop-color="#d9eef8"/>
    </linearGradient>
  </defs>
  <rect width="1024" height="1024" rx="72" fill="url(#fondo)"/>
  <circle cx="512" cy="360" r="190" fill="#2d6a4f"/>
  <path d="M405 365h214v138H405z" fill="#ffffff" opacity=".96"/>
  <path d="M512 235l245 118-245 118-245-118z" fill="#f4b942"/>
  <path d="M711 371v133" stroke="#f4b942" stroke-width="18" stroke-linecap="round"/>
  <circle cx="711" cy="523" r="25" fill="#f4b942"/>
  <text x="512" y="735" text-anchor="middle" font-family="Arial, sans-serif" font-size="38" font-weight="700" fill="#2d6a4f">ManabIA</text>
  <text x="512" y="805" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" font-weight="700" fill="#173f35">{titulo}</text>
  <text x="512" y="870" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" fill="#315b52">Ilustración educativa · modo simulado</text>
</svg>"""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _imagen_real(tema, texto):
    contexto = f" Basada también en este contexto: {texto}" if texto else ""
    prompt = (
        "Crea una ilustración educativa clara y amigable para explicar "
        f"{tema} a estudiantes de Manabí, Ecuador. Usa elementos visuales "
        "simples, inclusivos y culturalmente cercanos. Evita logotipos, marcas "
        f"de agua y bloques de texto.{contexto}"
    )
    response = OPENAI_CLIENT.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size="1024x1024",
    )
    if not getattr(response, "data", None):
        raise ValueError("OpenAI no devolvió una imagen.")
    imagen = response.data[0]
    b64_json = getattr(imagen, "b64_json", None)
    url = getattr(imagen, "url", None)
    if isinstance(b64_json, str) and b64_json:
        return f"data:image/png;base64,{b64_json}", "image/png"
    if isinstance(url, str) and url:
        return url, "image/png"
    raise ValueError("La respuesta de OpenAI no contiene una imagen utilizable.")


@app.get("/")
def home():
    return send_from_directory(str(CHAT_DIR), "chat.html")


@app.get("/panel")
@app.get("/panel/")
def panel():
    return send_from_directory(str(PANEL_DIR), "panel.html")


@app.get("/assets/<path:nombre>")
def assets(nombre):
    return send_from_directory(str(ASSETS_DIR), nombre)


@app.get("/api/estado")
def estado():
    modo = "real" if OPENAI_CLIENT is not None else "simulado"
    payload = {
        "nombre": "ManabIA",
        "estado": "disponible",
        "modo": modo,
        "openai_disponible": OPENAI_CLIENT is not None,
    }
    if OPENAI_STARTUP_NOTICE:
        payload["aviso"] = OPENAI_STARTUP_NOTICE
    return jsonify(payload)


@app.post("/api/explicar")
def explicar():
    data, error = _leer_json()
    if error:
        return error

    tema, error_tema = _leer_texto(data, "tema", requerido=True, maximo=200)
    texto, error_texto = _leer_texto(data, "texto", maximo=12000)
    if error_tema or error_texto:
        return _respuesta_error(error_tema or error_texto)

    if OPENAI_CLIENT is not None:
        try:
            explicacion_texto, pregunta = _explicacion_real(tema, texto)
            return _con_modo(
                {"explicacion": explicacion_texto, "pregunta": pregunta}, "real"
            )
        except Exception as exc:
            aviso = _aviso_fallo_openai(exc)
    else:
        aviso = OPENAI_STARTUP_NOTICE

    explicacion_texto, pregunta = _explicacion_simulada(tema, texto)
    return _con_modo(
        {"explicacion": explicacion_texto, "pregunta": pregunta},
        "simulado",
        aviso,
    )


@app.post("/api/evaluar")
def evaluar():
    data, error = _leer_json()
    if error:
        return error

    tema, error_tema = _leer_texto(data, "tema", requerido=True, maximo=200)
    pregunta, error_pregunta = _leer_texto(
        data, "pregunta", requerido=True, maximo=2000
    )
    respuesta, error_respuesta = _leer_texto(
        data, "respuesta", requerido=True, maximo=4000
    )
    estudiante, error_estudiante = _leer_texto(
        data,
        "estudiante",
        requerido=False,
        maximo=120,
        por_defecto="Estudiante anónimo",
    )
    intento_id, error_intento_id = _leer_texto(
        data,
        "intento_id",
        requerido=False,
        maximo=128,
    )
    error_validacion = (
        error_tema
        or error_pregunta
        or error_respuesta
        or error_estudiante
        or error_intento_id
    )
    if error_validacion:
        return _respuesta_error(error_validacion)
    if not estudiante:
        estudiante = "Estudiante anónimo"
    if not intento_id:
        intento_id = str(uuid.uuid4())

    # Una reconexión puede repetir el mismo POST. El primer request reserva el
    # identificador; los demás esperan brevemente y reciben el mismo resultado.
    with STATE_LOCK:
        resultado_guardado = copy.deepcopy(resultados_por_intento.get(intento_id))
        evento_en_curso = intentos_en_curso.get(intento_id)
        propietario = resultado_guardado is None and evento_en_curso is None
        if propietario:
            evento_en_curso = threading.Event()
            intentos_en_curso[intento_id] = evento_en_curso

    if resultado_guardado is not None:
        return jsonify(resultado_guardado)

    if not propietario:
        evento_en_curso.wait(timeout=20.0)
        with STATE_LOCK:
            resultado_guardado = copy.deepcopy(
                resultados_por_intento.get(intento_id)
            )
        if resultado_guardado is not None:
            return jsonify(resultado_guardado)
        return (
            jsonify(
                {
                    "error": "Evaluación en proceso",
                    "detalle": "Vuelve a intentar con el mismo intento_id.",
                    "intento_id": intento_id,
                }
            ),
            503,
        )

    try:
        if OPENAI_CLIENT is not None:
            try:
                semaforo, razon = _evaluacion_real(tema, pregunta, respuesta)
                modo = "real"
                aviso = None
            except Exception as exc:
                semaforo, razon = _evaluacion_simulada(tema, pregunta, respuesta)
                modo = "simulado"
                aviso = _aviso_fallo_openai(exc)
        else:
            semaforo, razon = _evaluacion_simulada(tema, pregunta, respuesta)
            modo = "simulado"
            aviso = OPENAI_STARTUP_NOTICE

        escalado, intentos = _registrar_evaluacion(
            estudiante, tema, pregunta, respuesta, semaforo, razon
        )
        payload = _payload_con_modo(
            {
                "semaforo": semaforo,
                "razon": razon,
                "escalado": escalado,
                "intentos": intentos,
                "intento_id": intento_id,
            },
            modo,
            aviso,
        )
        with STATE_LOCK:
            resultados_por_intento[intento_id] = copy.deepcopy(payload)
            evento = intentos_en_curso.pop(intento_id, None)
            if evento is not None:
                evento.set()
        return jsonify(payload)
    except Exception:
        with STATE_LOCK:
            evento = intentos_en_curso.pop(intento_id, None)
            if evento is not None:
                evento.set()
        raise


@app.get("/api/escalados")
def get_escalados():
    with STATE_LOCK:
        casos = copy.deepcopy(escalados)
    return jsonify({"escalados": casos})


@app.post("/api/generar_pregunta")
def generar_pregunta():
    data, error = _leer_json()
    if error:
        return error

    tema, error_tema = _leer_texto(data, "tema", requerido=True, maximo=200)
    contexto, error_contexto = _leer_texto(data, "contexto", maximo=12000)
    if not contexto and "texto" in data:
        contexto, error_contexto = _leer_texto(data, "texto", maximo=12000)
    dificultad, error_dificultad = _leer_texto(data, "dificultad", maximo=60)
    error_validacion = error_tema or error_contexto or error_dificultad
    if error_validacion:
        return _respuesta_error(error_validacion)

    if OPENAI_CLIENT is not None:
        try:
            pregunta = _pregunta_real(tema, contexto, dificultad)
            return _con_modo(pregunta, "real")
        except Exception as exc:
            aviso = _aviso_fallo_openai(exc)
    else:
        aviso = OPENAI_STARTUP_NOTICE

    pregunta = _pregunta_simulada(tema, contexto)
    return _con_modo(pregunta, "simulado", aviso)


@app.post("/api/generar_imagen")
def generar_imagen():
    data, error = _leer_json()
    if error:
        return error

    tema, error_tema = _leer_texto(data, "tema", requerido=True, maximo=200)
    texto, error_texto = _leer_texto(data, "texto", maximo=3000)
    if error_tema or error_texto:
        return _respuesta_error(error_tema or error_texto)

    if OPENAI_CLIENT is not None:
        try:
            imagen, mime_type = _imagen_real(tema, texto)
            return _con_modo(
                {
                    "imagen": imagen,
                    "url": imagen,
                    "mime_type": mime_type,
                },
                "real",
            )
        except Exception as exc:
            aviso = _aviso_fallo_openai(exc)
    else:
        aviso = OPENAI_STARTUP_NOTICE

    imagen = _svg_simulado(tema)
    return _con_modo(
        {
            "imagen": imagen,
            "url": imagen,
            "mime_type": "image/svg+xml",
        },
        "simulado",
        aviso,
    )


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=debug, port=port)
