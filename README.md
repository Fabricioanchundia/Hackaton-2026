# ManabIA

**Tutor educativo con inteligencia artificial y supervisión docente para el Buildathon Portoviejo, Tema 3 — ODS 4: Educación de calidad.**

ManabIA combina la identidad de Manabí con el acompañamiento de la IA. Es un prototipo educativo pensado para estudiantes de Portoviejo y otras comunidades donde la conectividad puede ser limitada o intermitente.

ManabIA **no es un juego**. Su núcleo es una tutoría personalizada: explica un tema, comprueba la comprensión, justifica cada evaluación y deriva al docente los casos que necesitan acompañamiento. La práctica grupal con turnos y marcador es una actividad de refuerzo integrada al flujo del tutor.

## Propuesta de valor

- Explica temas de distintas materias con lenguaje claro y ejemplos cercanos.
- Puede basar la explicación en un texto de clase pegado por el estudiante.
- Entrega evaluación formativa mediante un semáforo rojo, amarillo o verde y una razón comprensible.
- Conserva la trazabilidad de pregunta, respuesta, resultado, fecha e intento.
- Ofrece una práctica grupal después de verificar la comprensión.
- Escala automáticamente al panel docente tres respuestas rojas consecutivas del mismo estudiante en el mismo tema.
- Funciona en modo simulado sin clave ni consumo de OpenAI y usa ese mismo modo como respaldo si el servicio externo falla.
- Usa HTML, CSS y JavaScript sin frameworks, con Flask como único servidor.

## Relación con el ODS 4

El ODS 4 busca una educación inclusiva, equitativa y de calidad. ManabIA aporta a ese objetivo como una herramienta de apoyo: adapta la explicación al tema solicitado, ofrece retroalimentación inmediata, permite detectar dificultades repetidas y mantiene al docente como responsable del acompañamiento pedagógico.

El prototipo toma la brecha de acceso y conectividad rural de Manabí como motivación general. No pretende reemplazar infraestructura, políticas educativas ni trabajo docente; demuestra una forma de reducir la dependencia de servicios externos durante una tutoría.

## Flujo de aprendizaje

1. **Tutoría:** el estudiante indica su nombre, elige o escribe un tema y, opcionalmente, pega un texto de clase.
2. **Explicación:** ManabIA devuelve una explicación breve y una pregunta de comprobación.
3. **Evaluación trazable:** la respuesta recibe un semáforo y una razón. El `intento_id` permite reintentar una solicitud interrumpida sin contarla dos veces.
4. **Práctica integrada:** después de un resultado verde aparece **“Practicar lo aprendido (grupal)”**. Dos equipos responden por turnos cuatro preguntas de refuerzo dentro de la misma pantalla.
5. **Escalado:** tres resultados rojos consecutivos para la misma combinación estudiante–tema crean un caso docente una sola vez.
6. **Supervisión humana:** el panel presenta el estudiante, tema, motivo, última evidencia, cantidad de intentos y fecha para que una persona decida cómo intervenir.

## Arquitectura

```text
Navegador
├── /       Tutor, evaluación y práctica grupal integrada
├── /panel  Casos que requieren acompañamiento docente
└── /assets HTML/CSS/JavaScript sin proceso de compilación
        │
        ▼
Flask — Beckend/app.py
├── API educativa y validación de entradas
├── estado, historial e idempotencia en memoria
├── OpenAI opcional para texto, evaluación, preguntas e imágenes
└── simulación local automática y fallback por solicitud
```

Estructura del repositorio:

```text
Hackaton-2026/
├── Beckend/
│   └── app.py                 # Servidor Flask, API, OpenAI y modo simulado
├── Fronted/
│   ├── Chat/
│   │   └── chat.html          # Tutor y actividad de práctica integrada
│   ├── Panel/
│   │   └── panel.html         # Supervisión docente
│   ├── assets/
│   │   ├── chat.js            # Flujo de tutoría, reintentos y práctica
│   │   ├── panel.js           # Consulta segura y actualización del panel
│   │   └── styles.css         # Diseño responsivo compartido
│   └── app.ts                 # Archivo reservado; no se usa en ejecución
└── README.md
```

La escritura `Beckend` y `Fronted` forma parte de la estructura actual del repositorio; los comandos de este README usan esos nombres exactos.

## API

Todos los `POST` esperan `Content-Type: application/json`. Las respuestas generadas incluyen `modo: "real"` o `modo: "simulado"`; cuando ocurre un fallback también pueden incluir `aviso`.

| Método | Ruta | Entrada principal | Resultado |
|---|---|---|---|
| `GET` | `/api/estado` | — | Disponibilidad del servicio, modo activo y disponibilidad de OpenAI. |
| `POST` | `/api/explicar` | `tema`, `texto` opcional | `explicacion`, `pregunta`, `modo` y posible `aviso`. |
| `POST` | `/api/evaluar` | `tema`, `pregunta`, `respuesta`, `estudiante` opcional, `intento_id` opcional | `semaforo`, `razon`, `escalado`, `intentos`, `intento_id` y `modo`. |
| `POST` | `/api/generar_pregunta` | `tema`, `contexto` y `dificultad` opcionales | Pregunta, cuatro opciones, índice de respuesta correcta y explicación. |
| `POST` | `/api/generar_imagen` | `tema`, `texto` opcional | Imagen como URL o data URI, además de su tipo MIME. |
| `GET` | `/api/escalados` | — | Lista de casos escalados con evidencia y trazabilidad. |

En modo real, `/api/generar_pregunta` usa **function calling real de OpenAI**: declara la herramienta `crear_pregunta_practica`, obliga al modelo a llamarla y valida sus argumentos contra la estructura esperada. No depende de pedir JSON libre y extraerlo manualmente del texto.

`/api/generar_imagen` está disponible como capacidad complementaria; la interfaz principal actual no solicita imágenes automáticamente.

### Ejemplo de evaluación

```json
{
  "tema": "fracciones",
  "pregunta": "Si una torta se divide en 4 partes iguales, ¿qué representa 1/4?",
  "respuesta": "Representa una de las cuatro partes iguales de la torta.",
  "estudiante": "Ana",
  "intento_id": "demo-ana-fracciones-001"
}
```

El cliente debe reutilizar el mismo `intento_id` cuando reenvía una evaluación por timeout o reconexión. Así, una misma respuesta no aumenta dos veces el historial ni activa un escalado incorrecto.

## Modos de ejecución y tolerancia a fallos

| Situación | Comportamiento |
|---|---|
| No existe `OPENAI_API_KEY` | Inicia directamente en modo simulado. |
| La clave y OpenAI están disponibles | Usa los modelos configurados y responde en modo real. |
| OpenAI falla o supera el tiempo de espera | Completa esa solicitud con la respuesta simulada e informa el fallback. |
| El navegador pierde conexión con Flask | Conserva el estado visible, muestra el problema y permite reintentar. |

El modo simulado permite demostrar explicación, evaluación, semáforos, práctica, imágenes ilustrativas y escalado sin gastar créditos. No significa que la aplicación web funcione sin poder alcanzar el servidor Flask: esa separación se mantiene como una limitación del prototipo.

## Requisitos

- Python 3.10 o posterior recomendado.
- Un navegador moderno.
- Paquetes de Python: `Flask` y `openai`.
- Clave de OpenAI solo si se desea probar el modo real.

No se requiere Node.js, base de datos, autenticación ni proceso de compilación para ejecutar la aplicación.

## Instalación y ejecución

### Windows PowerShell

```powershell
cd C:\ruta\al\repositorio\Hackaton-2026
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install Flask openai
python Beckend/app.py
```

### macOS o Linux

```bash
cd /ruta/al/repositorio/Hackaton-2026
python3 -m venv .venv
source .venv/bin/activate
python -m pip install Flask openai
python Beckend/app.py
```

Con el servidor activo, abre:

- Tutor: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- Panel docente: [http://127.0.0.1:5000/panel](http://127.0.0.1:5000/panel)
- Estado de la API: [http://127.0.0.1:5000/api/estado](http://127.0.0.1:5000/api/estado)

No abras `chat.html` directamente ni levantes el frontend en otro puerto: las vistas y la API están diseñadas para compartir el mismo origen de Flask.

## Configuración opcional de OpenAI

Las tres variables son opcionales. Si se omite `OPENAI_API_KEY`, ManabIA inicia en modo simulado.

| Variable | Uso | Valor predeterminado |
|---|---|---|
| `OPENAI_API_KEY` | Habilita las llamadas reales a OpenAI. | Sin valor; activa simulación. |
| `OPENAI_MODEL` | Modelo de texto para explicación, evaluación y preguntas. | `gpt-4o-mini` |
| `OPENAI_IMAGE_MODEL` | Modelo para ilustraciones educativas. | `gpt-image-1-mini` |

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "tu_clave"
$env:OPENAI_MODEL = "gpt-4o-mini"
$env:OPENAI_IMAGE_MODEL = "gpt-image-1-mini"
python Beckend/app.py
```

macOS o Linux:

```bash
export OPENAI_API_KEY="tu_clave"
export OPENAI_MODEL="gpt-4o-mini"
export OPENAI_IMAGE_MODEL="gpt-image-1-mini"
python Beckend/app.py
```

Las variables se leen al iniciar el proceso. Reinicia Flask después de cambiarlas y nunca publiques una clave real en el repositorio.

## Guion de prueba manual

1. Arranca el servidor sin `OPENAI_API_KEY` y confirma en `/api/estado` que el modo sea `simulado`.
2. Abre `/`, escribe **Ana**, selecciona **Fracciones** y pulsa **Empezar a aprender**.
3. Responde: “1/4 representa una de las cuatro partes iguales de la torta”. Debe aparecer un semáforo verde con una razón.
4. Pulsa **Practicar lo aprendido (grupal)** y completa los cuatro turnos de los equipos Ceibo y Colibrí.
5. Inicia otro tema con un estudiante de prueba y responde “No sé” tres veces consecutivas. El tercer resultado debe informar el escalado.
6. Abre `/panel` y comprueba que aparezcan el estudiante, tema, motivo, última respuesta, intentos y fecha.
7. Detén temporalmente Flask o simula una conexión lenta para comprobar los mensajes de error y los botones de reintento.
8. Si dispones de una clave, reinicia con `OPENAI_API_KEY` y verifica que el indicador cambie a modo real. Una falla de OpenAI debe devolver la experiencia al modo simulado sin cortar el flujo.

Para una comprobación rápida desde PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/estado
```

O desde macOS/Linux:

```bash
curl http://127.0.0.1:5000/api/estado
```

## Supervisión humana

La supervisión docente no es decorativa: forma parte del flujo central. El backend agrupa el historial por estudiante y tema; cuando detecta tres rojos consecutivos, registra un caso con su motivo y evidencia. El panel permite que el docente priorice ese caso y decida el apoyo adecuado.

La IA entrega retroalimentación formativa, pero **no asigna una calificación oficial, no sanciona y no toma la decisión pedagógica final**. El panel actual es de consulta; la intervención y el cierre del caso ocurren fuera del prototipo y quedan a cargo del docente.

## Limitaciones del prototipo

- El historial, la idempotencia y los casos escalados viven en memoria; se pierden al reiniciar Flask y no se comparten entre varios procesos.
- No existe autenticación ni separación de roles. El tutor y el panel deben usarse solo con datos de demostración en un entorno controlado.
- No hay base de datos externa, sincronización offline ni instalación como PWA.
- El fallback cubre la indisponibilidad de OpenAI, no una pérdida total de conexión entre el navegador y Flask.
- En modo real, los textos enviados pueden procesarse mediante OpenAI; no deben usarse datos sensibles de estudiantes sin las autorizaciones y políticas correspondientes.
- La evaluación y el contenido generados por IA pueden equivocarse y requieren criterio docente.
- La actividad de práctica recibe el índice correcto en el navegador para calcular el marcador; no es un mecanismo de examen seguro.
- Es una aplicación de demostración para el buildathon, no un servicio endurecido para producción.

## Equipo

- **Fabricio:** backend y agente educativo.
- **Jhon:** frontend del tutor y chat.
- **Kalil Mera:** frontend de actividades, evidencia y pitch.

---

**ManabIA — hecho en Manabí para aprender sin barreras.**
