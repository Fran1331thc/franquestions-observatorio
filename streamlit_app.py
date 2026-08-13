"""Entrada publica estable del Observatorio FranQuestions.

Streamlit ejecuta este archivo en cada interaccion.
"""

from pathlib import Path
from runpy import run_path

# Marcador para reiniciar la version estable.
PUBLIC_RELEASE = "2.12.3"

run_path(str(Path(__file__).with_name("streamlit_app_stable.py")), run_name="__main__")
