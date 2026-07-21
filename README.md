# Kosko

**Tutor educativo con inteligencia artificial y supervisión docente**
Buildathon Portoviejo · Tema 3 (Impacto global desde Portoviejo) · ODS 4 — Educación de Calidad

Equipo: Fabricio (backend/agente) · Jhon (frontend estudiante) · Kalil Mera (frontend docente / evidencia)

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