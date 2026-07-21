# Kosko

**Tutor educativo con inteligencia artificial y supervisión docente**
Buildathon Portoviejo · Tema 3 (Impacto global desde Portoviejo) · ODS 4 — Educación de Calidad

<<<<<<< HEAD
Equipo: Fabricio (backend/agente) · Jhon (frontend estudiante) · Kalil Mera (frontend docente / evidencia)
=======
## ODS 4: Educación de calidad
KOSKA es un prototipo educativo creado en Portoviejo para apoyar el aprendizaje mediante explicaciones claras, evaluación formativa y práctica guiada. La IA personaliza la experiencia de aprendizaje y ayuda a detectar dificultades; el docente conserva la decisión pedagógica final.

El proyecto se alinea con el **Objetivo de Desarrollo Sostenible 4**, que busca garantizar una educación inclusiva, equitativa y de calidad. Koska responde a las brechas de acompañamiento educativo que pueden afectar a estudiantes de zonas rurales de Manabí, ofreciendo una experiencia de aprendizaje personalizada y una herramienta de supervisión para docentes.
> KOSKA no es un juego. La actividad grupal de práctica es un recurso de refuerzo integrado al flujo de tutoría.

## Problema

Las diferencias en acceso a recursos educativos y acompañamiento personalizado pueden profundizar las dificultades de aprendizaje. Cuando un estudiante no logra comprender un tema, el docente no siempre recibe una señal temprana y clara para intervenir.
En contextos con acceso desigual a recursos educativos y acompañamiento personalizado, las dificultades de aprendizaje pueden pasar desapercibidas y acumularse. Esto puede afectar con mayor intensidad a estudiantes de zonas rurales y comunidades con infraestructura tecnológica desigual.

## Solución
KOSKA busca ofrecer retroalimentación oportuna al estudiante y señales claras al docente para intervenir ante una dificultad repetida.

Koska integra un flujo de tutoría educativa:
## ODS 4: Educación de calidad

KOSKA se alinea con el **Objetivo de Desarrollo Sostenible 4: garantizar una educación inclusiva, equitativa y de calidad**. Aporta a este objetivo mediante:

- Explicación de temas escolares con IA en lenguaje simple.
- Evaluación de respuestas mediante un semáforo de comprensión: rojo, amarillo o verde, con una razón justificada.
- Escalamiento al panel docente cuando un estudiante obtiene tres alertas rojas consecutivas en el mismo tema.
- Actividad grupal **“Practica lo aprendido”**, con turnos, puntaje y retroalimentación inmediata.
- Pre-reportes individuales que el docente puede revisar y editar antes de definir la retroalimentación final.
- Explicaciones adaptadas al tema que estudia cada estudiante.
- Retroalimentación inmediata y comprensible sobre sus respuestas.
- Identificación temprana de dificultades recurrentes.
- Supervisión humana para que el docente revise y decida la intervención educativa.

La solución nace desde el contexto de Portoviejo y Manabí, pero su modelo puede adaptarse a otros territorios, materias y niveles educativos.

## Solución construida

KOSKA integra el siguiente flujo de aprendizaje:

La inteligencia artificial apoya la personalización del aprendizaje, pero la decisión pedagógica final se mantiene en manos del docente.
1. **Tutoría con IA:** el estudiante ingresa su nombre, selecciona o escribe un tema y puede añadir un texto de clase como contexto.
2. **Explicación y comprobación:** el tutor entrega una explicación breve y una pregunta para verificar la comprensión.
3. **Semáforo de comprensión:** la respuesta recibe un resultado verde, amarillo o rojo junto con una razón justificada.
4. **Escalamiento docente:** tres resultados rojos consecutivos para un mismo estudiante y tema crean un caso visible en el panel docente.
5. **Práctica integrada:** después de verificar la comprensión, el estudiante puede acceder a “Practicar lo aprendido (grupal)”, una actividad por turnos con preguntas, puntaje y retroalimentación.
6. **Panel docente:** permite consultar los casos escalados y revisar la evidencia que originó la alerta.

## Arquitectura

| Componente | Tecnología | Función |
| --- | --- | --- |
| Backend | Python + Flask | Explicaciones, evaluación, semáforo y escalamiento docente. |
| IA | OpenAI API | Generación de explicaciones y evaluación de comprensión. |
| Chat estudiantil | HTML, CSS y JavaScript | Interacción principal con el tutor. |
| Actividad de práctica | HTML, CSS y JavaScript | Práctica colaborativa y retroalimentación. |
| Panel docente | HTML, CSS y JavaScript | Visualización de casos escalados y pre-reportes. |
```text
Navegador
├── /             Chat del tutor y actividad de práctica
├── /panel        Panel de supervisión docente
└── /assets       JavaScript y estilos de la interfaz
        │
        ▼
Flask — Beckend/app.py
├── API educativa y validación de datos
├── Historial de evaluaciones y escalamiento en memoria
├── OpenAI API para explicación, evaluación, preguntas e imágenes
└── Modo simulado cuando OpenAI no está disponible o falla
```

## Herramientas de OpenAI

- **OpenAI API con GPT:** utilizada para generar explicaciones educativas y evaluar la comprensión del estudiante.
- **Codex:** utilizado durante el desarrollo y la mejora del prototipo.
- **OpenAI API con GPT:** genera explicaciones y evalúa la comprensión del estudiante.
- **Function calling:** genera preguntas de práctica con cuatro opciones, una respuesta correcta y explicación validada.
- **OpenAI Images:** permite generar una imagen ilustrativa del concepto solicitado.
- **Codex:** utilizado durante el desarrollo del prototipo.

## Métrica de impacto propuesta
Cuando no existe una clave de OpenAI o una llamada al servicio falla, el backend responde con contenido simulado para mantener el flujo de demostración. Esto no implica funcionamiento sin internet: el navegador necesita conectarse al servidor Flask.

Koska permite medir el número de estudiantes que mejoran su semáforo de comprensión después de una práctica y el número de alertas rojas que reciben seguimiento docente. Esta evidencia permite observar si el sistema ayuda a identificar dificultades y promover intervenciones oportunas.
## API

## Cómo ejecutar
Todos los endpoints `POST` reciben datos JSON.

1. Instalar las dependencias:
| Método | Ruta | Función |
| --- | --- | --- |
| `GET` | `/api/estado` | Informa el estado del servicio y el modo activo. |
| `POST` | `/api/explicar` | Genera una explicación y una pregunta de comprobación. |
| `POST` | `/api/evaluar` | Evalúa una respuesta, asigna semáforo y registra el intento. |
| `GET` | `/api/escalados` | Devuelve los casos que requieren acompañamiento docente. |
| `POST` | `/api/generar_pregunta` | Genera una pregunta de práctica de opción múltiple. |
| `POST` | `/api/generar_imagen` | Genera una imagen ilustrativa para un tema. |

   ```bash
   pip install flask openai
   ```
### Ejemplo de evaluación

2. Configurar la clave de OpenAI:
```json
{
  "tema": "fracciones",
  "pregunta": "Si una torta se divide en cuatro partes iguales, ¿qué representa 1/4?",
  "respuesta": "Una de las cuatro partes iguales.",
  "estudiante": "Ana",
  "intento_id": "demo-ana-fracciones-001"
}
```

   ```bash
   set OPENAI_API_KEY=tu_clave_aqui
   ```
El campo `intento_id` permite reenviar una evaluación interrumpida sin duplicar su registro ni activar un escalamiento incorrecto.

3. Ejecutar el backend:
## Estructura del repositorio

   ```bash
   cd Beckend
   python app.py
   ```
```text
Hackaton-2026/
├── Beckend/
│   ├── app.py                    # Servidor Flask y API educativa
│   └── requirements.txt           # Dependencias del backend
├── Fronted/
│   ├── Chat/
│   │   └── chat.html              # Interfaz del tutor estudiantil
│   ├── Panel/
│   │   └── panel.html             # Panel de supervisión docente
│   ├── assets/
│   │   ├── chat.js                # Lógica del chat y práctica
│   │   ├── panel.js               # Lógica del panel docente
│   │   └── styles.css             # Estilos compartidos
│   ├── juego/
│   │   └── unirse.html            # Vista para unirse a la práctica
│   └── app.ts
├── .gitignore
├── README.md
└── requirements.txt
```

## Requisitos

- Python 3.10 o superior recomendado.
- Navegador moderno.
- Paquetes Python: `flask` y `openai`.
- Clave `OPENAI_API_KEY` solo para utilizar las funciones reales de OpenAI.

No se requiere Node.js, autenticación ni una base de datos externa para ejecutar el prototipo.

## Instalación y ejecución

### Windows PowerShell

```powershell
git clone https://github.com/Fabricioanchundia/Hackaton-2026.git
cd Hackaton-2026
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r Beckend\requirements.txt
python Beckend\app.py
```

### macOS o Linux

```bash
git clone https://github.com/Fabricioanchundia/Hackaton-2026.git
cd Hackaton-2026
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r Beckend/requirements.txt
python Beckend/app.py
```

Con el servidor activo, abre:

- Tutor: `http://127.0.0.1:5000/`
- Panel docente: `http://127.0.0.1:5000/panel`
- Estado de la API: `http://127.0.0.1:5000/api/estado`

## Configuración opcional de OpenAI

Para utilizar el modo real, configura la clave antes de iniciar Flask:

4. Abrir en el navegador las interfaces ubicadas en `Fronted/Chat`, `Fronted/Juego` y `Fronted/Panel`.
```powershell
$env:OPENAI_API_KEY = "tu_clave_de_openai"
python Beckend\app.py
```

También se pueden configurar los modelos mediante `OPENAI_MODEL` y `OPENAI_IMAGE_MODEL`. Nunca se debe publicar una clave real en el repositorio.

## Supervisión humana y uso responsable

La IA entrega apoyo formativo, pero **no asigna calificaciones oficiales, no sanciona estudiantes ni reemplaza la decisión docente**. Los casos escalados deben ser revisados por una persona antes de decidir cualquier acción pedagógica.

El prototipo trabaja con información en memoria. No se deben enviar datos sensibles de estudiantes sin autorización, políticas de privacidad y medidas de protección adecuadas.

## Métrica de impacto propuesta

La evidencia de impacto de KOSKA se puede medir mediante:

- Porcentaje de estudiantes que mejoran su semáforo de comprensión después de practicar.
- Número de alertas rojas detectadas y revisadas por un docente.
- Cantidad de casos escalados por tema, para orientar refuerzos educativos.
- Tiempo entre la detección de una dificultad y la intervención docente.

Estas métricas muestran si la solución ayuda a identificar dificultades a tiempo y favorece un acompañamiento educativo más oportuno.

## Limitaciones actuales

- El historial y los casos escalados se almacenan en memoria; se pierden al reiniciar Flask.
- No incluye autenticación, base de datos externa ni separación de roles para producción.
- La aplicación requiere comunicación entre el navegador y el servidor Flask.
- Las respuestas y evaluaciones generadas por IA pueden equivocarse y deben revisarse con criterio docente.
- La actividad de práctica no es un mecanismo de evaluación segura o calificación oficial.

## Escalabilidad

Aunque nace para el contexto educativo de Portoviejo y Manabí, Koska puede adaptarse a otros territorios cambiando contenidos, ejemplos locales y necesidades curriculares. Su modelo de tutoría personalizada con supervisión humana puede aplicarse a distintos niveles y materias.
KOSKA puede escalar a otros territorios adaptando contenidos, ejemplos y currículos locales. Su enfoque combina tutoría personalizada, evidencia de comprensión y supervisión humana, por lo que puede aplicarse a distintas materias, grados y contextos educativos.

## Equipo

- **Fabricio:** backend y agente educativo.
- **Jhon:** frontend del chat.
- **Kalil Mera:** actividad de práctica, evidencia y pitch.
>>>>>>> 6e405b0b9033a1391006292efecbcaca6a148d66

---

## 1. El problema

Un estudio de la Universidad Técnica de Manabí identificó una brecha del 9% entre
estudiantes urbanos y rurales en habilidades digitales, que se traduce en desventajas
académicas concretas. Otro estudio de campo en el cantón Rocafuerte, Manabí, encontró
que la ausencia total de internet en instituciones educativas rurales refuerza la
dependencia de metodologías tradicionales, limitando el aprendizaje fuera del aula.

## 2. Qué es Kosko

Kosko es un **tutor educativo con IA**, no un juego. Explica cualquier tema, comprueba
que el estudiante entendió, y deriva al docente los casos que necesitan acompañamiento
real. La práctica en equipo es una actividad de refuerzo integrada al flujo del tutor,
no el centro del producto.

**Diseñado pensando en conectividad limitada o intermitente**, común en zonas rurales
de Manabí.

## 3. Cómo funciona (flujo completo)

1. **Bienvenida:** el estudiante entra a la landing y hace clic en "Abrir chat con Kosko".
2. **Aprende:** escribe su nombre, elige una categoría (Matemática, Biología, Física,
   Lenguaje u otra) y escribe el tema específico que quiere aprender.
3. **Comprueba:** Kosko explica el tema y hace una pregunta de verificación. La respuesta
   del estudiante se evalúa con un semáforo (🔴 rojo / 🟡 amarillo / 🟢 verde) y una razón
   justificada — esto es lo que hace las decisiones **trazables**.
4. **Practica:** si la respuesta es verde, aparece el botón "Practicar lo aprendido
   (grupal)", una actividad de refuerzo con preguntas de opción múltiple.
5. **Escalado automático:** si un estudiante acumula 3 respuestas rojas seguidas en el
   mismo tema, el caso se envía automáticamente al Panel Docente con el motivo, la última
   respuesta y el número de intentos — así el docente decide cómo intervenir. Esto es la
   **supervisión humana** que pide el reto.

## 4. Acceso al Panel Docente

El panel (`/panel`) muestra información de estudiantes, así que no es de acceso libre
para cualquiera que abra el link.

- **Clave de acceso:** `kosko2026`
- Esto es una barrera de intención para la demo (no es seguridad de nivel producción):
  demuestra el concepto de que solo el docente entra a supervisar. La clave se puede
  cambiar en `Fronted/assets/panel.js`, en la constante `DOCENTE_ACCESS_CODE`.

## 5. Arquitectura

```text
Navegador
├── /        Landing + Tutor (aprender, comprobar, practicar)
├── /panel   Acceso con clave + supervisión docente
└── /assets  HTML/CSS/JavaScript sin frameworks ni proceso de build
        │
        ▼
Flask — Beckend/app.py
├── API educativa y validación de entradas
├── Estado, historial e idempotencia en memoria
├── OpenAI (gpt-4o-mini para texto, DALL·E para imágenes) — opcional
└── Modo simulado automático si falta la key o si OpenAI falla en una petición
```

### Estructura de carpetas

```text
Hackaton-2026/
├── api/
│   └── index.py            # Punto de entrada para desplegar en Vercel
├── Beckend/
│   ├── app.py               # Servidor Flask, toda la lógica del backend
│   ├── .env                 # API key real (NO se sube a git)
│   └── requirements.txt
├── Fronted/
│   ├── Chat/chat.html       # Tutor del estudiante
│   ├── Panel/panel.html     # Supervisión docente (protegido con clave)
│   └── assets/
│       ├── chat.js
│       ├── panel.js
│       └── styles.css
├── vercel.json               # Configuración de despliegue en Vercel
├── requirements.txt
└── README.md
```

## 6. Paleta de colores

Colores asociados a educación y confianza (azul), con acento cálido (ámbar):

| Uso | Color |
|---|---|
| Azul primario (marca, botones) | `#123a5e` |
| Azul medio (acentos) | `#1d5c8a` / `#2e86c1` |
| Ámbar (destacados, CTA secundario) | `#f2a93b` |
| Verde (solo semáforo "correcto" / conexión activa — significado universal) | `#117344` |

Tipografía: **Poppins** en toda la interfaz.

## 7. API

Todos los `POST` esperan `Content-Type: application/json`. Las respuestas incluyen
`modo: "real"` o `modo: "simulado"`, y pueden incluir `aviso` si hubo un fallback.

| Método | Ruta | Entrada | Resultado |
|---|---|---|---|
| GET | `/api/estado` | — | Modo activo, disponibilidad de OpenAI |
| POST | `/api/explicar` | `tema`, `texto` opcional | `explicacion`, `pregunta` |
| POST | `/api/evaluar` | `tema`, `pregunta`, `respuesta`, `estudiante` opcional | `semaforo`, `razon`, `escalado`, `intentos` |
| GET | `/api/escalados` | — | Lista de casos para el panel docente |
| POST | `/api/generar_pregunta` | `tema`, `contexto` opcional | Pregunta de práctica (function calling real) |
| POST | `/api/generar_imagen` | `tema` | Imagen ilustrativa (DALL·E o SVG simulado) |

## 8. Cómo correrlo localmente (recomendado para la demo)

```bash
cd Beckend
pip install -r requirements.txt
```

Crea el archivo `Beckend/.env` con tu key real:
```
OPENAI_API_KEY=sk-proj-tu_key_real_aqui
```

Corre:
```bash
python app.py
```

- Estudiante: `http://localhost:5000/`
- Docente: `http://localhost:5000/panel` (clave: `kosko2026`)

Si no configuras la key, el programa funciona igual en **modo simulado** — útil para
practicar y ensayar antes del evento sin gastar créditos.

## 9. Despliegue en Vercel (opcional)

El proyecto incluye `api/index.py` y `vercel.json` para desplegarse en Vercel.

⚠️ **Importante:** Vercel usa funciones sin estado (serverless). El historial y los
casos escalados se guardan en memoria, así que pueden no persistir de forma confiable
entre peticiones en producción. **Para la demo del jurado, se recomienda correr el
proyecto localmente** (paso 8) y usar el link de Vercel solo como evidencia de que el
proyecto es desplegable.

Pasos:
1. Sube el repo a GitHub.
2. En Vercel: "Add New" → "Project" → selecciona el repo.
3. En "Environment Variables", agrega `OPENAI_API_KEY` con tu key real.
4. Deploy.

## 10. Requisito de supervisión humana (cumplimiento explícito)

Kosko nunca reemplaza al docente. El agente actúa como primer filtro: explica, evalúa
y practica con el estudiante, pero cuando detecta una dificultad sostenida (3 rojos
seguidos), se detiene y pasa el caso a una persona real, con contexto suficiente para
decidir cómo intervenir.