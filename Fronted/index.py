"""
Punto de entrada para Vercel.
Vercel busca una variable llamada "app" que sea una aplicación WSGI —
aquí simplemente importamos la app de Flask que ya existe en Beckend/app.py,
sin modificar ni duplicar su lógica.
"""
import os
import sys

# Agrega la carpeta Beckend al path para poder importar app.py tal cual está
BECKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Beckend")
sys.path.insert(0, BECKEND_DIR)

from app import app  # noqa: E402  (import intencional después de ajustar el path)