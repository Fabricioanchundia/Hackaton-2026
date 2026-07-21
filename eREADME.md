# KOSKA

**Tutor educativo con inteligencia artificial y supervisión docente para el Buildathon Portoviejo — ODS 4: Educación de calidad.**

KOSKA es un prototipo de tutoría educativa que ayuda a estudiantes a comprender contenidos escolares con explicaciones sencillas, evaluación formativa y práctica guiada. La inteligencia artificial apoya el aprendizaje personalizado; el docente conserva la decisión final sobre el acompañamiento pedagógico.

## ODS 4: Educación de calidad

KOSKA se alinea con el **Objetivo de Desarrollo Sostenible 4**, que busca garantizar una educación inclusiva, equitativa y de calidad. El proyecto responde a las dificultades de acompañamiento que pueden profundizar las brechas de aprendizaje en contextos rurales de Manabí, mediante retroalimentación inmediata y alertas tempranas para el docente.

## Problema

Cuando un estudiante no comprende un tema, su dificultad puede pasar desapercibida hasta acumularse. Las diferencias en acceso a recursos educativos y acompañamiento personalizado agravan este problema, especialmente en comunidades con infraestructura tecnológica desigual.

## Solución

KOSKA integra un flujo de aprendizaje completo:

- Explica temas escolares como fracciones, fotosíntesis y verbos en pasado con lenguaje claro.
- Evalúa la respuesta del estudiante mediante un semáforo: rojo, amarillo o verde, acompañado de una razón.
- Registra los resultados por tema y escala un caso al panel docente cuando detecta tres resultados rojos consecutivos.
- Incluye **“Practica lo aprendido”**, una actividad grupal con turnos, puntaje y retroalimentación en cada respuesta.
- Genera pre-reportes individuales de la práctica para que el docente los revise y edite.

KOSKA no es un juego: la práctica es una actividad de refuerzo dentro de un sistema de tutoría y seguimiento educativo.

## Supervisión humana

La supervisión docente es parte central de KOSKA. La IA proporciona explicaciones y retroalimentación formativa, pero no asigna calificaciones oficiales ni toma decisiones pedagógicas finales. Cuando se identifican dificultades repetidas, el sistema las presenta al docente para que este revise el caso y defina el apoyo adecuado.

## Arquitectura

| Componente | Tecnología | Función |
| --- | --- | --- |
| Backend | Python y Flask | Explicación, evaluación, semáforo y escalamiento de casos. |
| IA | OpenAI API con GPT | Generación de explicaciones y evaluación de comprensión. |
| Chat estudiantil | HTML, CSS y JavaScript | Interfaz principal de tutoría. |
| Actividad de práctica | HTML, CSS y JavaScript | Refuerzo colaborativo con preguntas y retroalimentación. |
| Panel docente | HTML, CSS y JavaScript | Consulta de casos escalados y pre-reportes. |

## Herramientas de OpenAI

- **OpenAI API con GPT:** empleada para las explicaciones y la evaluación de la comprensión.
- **Codex:** utilizado durante el desarrollo del prototipo.

## Métrica de impacto propuesta

La evidencia de impacto se puede medir mediante:

- Número de estudiantes que mejoran su resultado de comprensión después de practicar.
- Número de alertas rojas detectadas y revisadas por un docente.
- Temas con mayor recurrencia de dificultades, para orientar refuerzos educativos.

Estas métricas permiten demostrar si KOSKA ayuda a detectar a tiempo necesidades de aprendizaje y a facilitar intervenciones docentes más oportunas.

## Estructura del proyecto

```text
Hackaton-2026/
├── Beckend/
│   └── app.py
├── Fronted/
│   ├── Chat/chat.html
│   ├── Juego/juego.html
│   └── Panel/panel.html
├── EVIDENCIA_PITCH_KALIL.md
└── README.md
```

## Ejecución

### Requisitos

- Python 3.
- Paquetes `flask` y `openai`.
- Variable de entorno `OPENAI_API_KEY` para usar las funciones basadas en OpenAI.

### Comandos

```powershell
cd Hackaton-2026
python -m pip install flask openai
$env:OPENAI_API_KEY = "tu_clave_de_openai"
python Beckend/app.py
```

Después de iniciar el servidor, abre las interfaces ubicadas en `Fronted/Chat`, `Fronted/Juego` y `Fronted/Panel`.

## Limitaciones actuales

- El historial de evaluaciones y los casos escalados se almacenan en memoria y se pierden al reiniciar el servidor.
- El prototipo requiere conexión entre el navegador y el servidor Flask; no se declara funcionamiento sin internet.
- No incorpora autenticación, base de datos externa ni gestión de datos sensibles para producción.
- Las respuestas generadas por IA deben ser revisadas con criterio docente.

## Escalabilidad

KOSKA nace en Portoviejo, con atención a las necesidades educativas de Manabí, pero puede adaptarse a otros territorios. Sus contenidos, ejemplos y temas pueden ajustarse a distintos currículos y contextos, manteniendo el modelo de aprendizaje personalizado con supervisión humana.

## Equipo

- **Fabricio:** backend y agente educativo.
- **Jhon:** frontend del chat.
- **Kalil Mera:** actividad de práctica, evidencia y pitch.

---

**KOSKA — tecnología educativa con IA, acompañada por docentes.**
