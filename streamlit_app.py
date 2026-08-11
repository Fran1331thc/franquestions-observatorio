"""Entrada pública estable del Observatorio FranQuestions.

Streamlit vuelve a ejecutar este archivo en cada interacción. ``run_path``
garantiza que la implementación completa también se ejecute de nuevo, en vez
de quedar retenida en la caché de importaciones de Python y producir una
pantalla vacía después de ciertas recargas.
"""

from pathlib import Path
from runpy import run_path


run_path(str(Path(__file__).with_name("streamlit_app_stable.py")), run_name="__main__")
