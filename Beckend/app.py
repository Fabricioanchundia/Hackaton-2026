"""
TutorIA Rural - Backend
Equipo: Fabricio (agente) / Jhon (chat) / Kalil Mera (panel docente)

Cómo correrlo:
1. pip install flask openai
2. export OPENAI_API_KEY="tu_key_aqui"
3. python app.py
4. Abrir static/chat.html para el estudiante
5. Abrir static/panel.html para el docente
"""

from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import os
import json

app = Flask(__name__, static_folder="static")
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------------------------------------------------------------
# "Base de datos" en memoria (suficiente para la demo de 2 horas)
# ---------------------------------------------------------------
# historial[tema] = lista de resultados ("rojo"/"amarillo"/"verde")
historial = {}
# casos escalados al docente (esto es lo que consume el panel de Kalil)
escalados = []


# ---------------------------------------------------------------
# FABRICIO: prompt del sistema del agente
# ---------------------------------------------------------------
SYSTEM_PROMPT = """Eres TutorIA, un tutor educativo para estudiantes rurales de Ecuador.
Explicas conceptos en lenguaje simple y cercano, con ejemplos cotidianos.
Después de explicar, SIEMPRE haces 1-2 preguntas cortas para verificar comprensión.
Sé breve: máximo 4-5 líneas por explicación.
"""


@app.route("/")
def home():
    return send_from_directory("static", "chat.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


# ---------------------------------------------------------------
# ENDPOINT 1: explicar un concepto (lo usa el chat de Jhon)
# ---------------------------------------------------------------
@app.route("/api/explicar", methods=["POST"])
def explicar():
    data = request.json
    tema = data.get("tema", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Explícame el tema: {tema}"},
        ],
    )

    explicacion = response.choices[0].message.content
    return jsonify({"explicacion": explicacion})


# ---------------------------------------------------------------
# ENDPOINT 2: evaluar la respuesta del estudiante -> semáforo
# (FABRICIO: esta es la función central del reto)
# ---------------------------------------------------------------
@app.route("/api/evaluar", methods=["POST"])
def evaluar():
    data = request.json
    tema = data.get("tema", "")
    pregunta = data.get("pregunta", "")
    respuesta_estudiante = data.get("respuesta", "")

    # Le pedimos al modelo que responda en JSON estricto
    eval_prompt = f"""
Eres un evaluador educativo. El estudiante respondió a esta pregunta sobre "{tema}":

Pregunta: {pregunta}
Respuesta del estudiante: {respuesta_estudiante}

Evalúa la comprensión y responde SOLO en JSON con este formato exacto, sin texto adicional:
{{"semaforo": "rojo" o "amarillo" o "verde", "razon": "explicación breve de por qué, en 1 frase"}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": eval_prompt}],
    )

    contenido = response.choices[0].message.content.strip()
    # Limpieza por si el modelo agrega ```json
    contenido = contenido.replace("```json", "").replace("```", "").strip()

    try:
        resultado = json.loads(contenido)
    except json.JSONDecodeError:
        resultado = {"semaforo": "amarillo", "razon": "No se pudo evaluar con certeza"}

    # Registrar en el historial del tema
    historial.setdefault(tema, []).append(resultado["semaforo"])

    # Revisar si hay que escalar (3 rojos seguidos en el mismo tema)
    escalado_ahora = False
    ultimos = historial[tema][-3:]
    if len(ultimos) == 3 and all(s == "rojo" for s in ultimos):
        caso = {
            "tema": tema,
            "motivo": f"3 respuestas seguidas en rojo. Última razón: {resultado['razon']}",
            "estudiante": data.get("estudiante", "Estudiante anónimo"),
        }
        escalados.append(caso)
        escalado_ahora = True

    return jsonify({
        "semaforo": resultado["semaforo"],
        "razon": resultado["razon"],
        "escalado": escalado_ahora,
    })


# ---------------------------------------------------------------
# ENDPOINT 3: lista de casos escalados (lo usa el panel de Kalil)
# ---------------------------------------------------------------
@app.route("/api/escalados", methods=["GET"])
def get_escalados():
    return jsonify({"escalados": escalados})


if __name__ == "__main__":
    app.run(debug=True, port=5000)