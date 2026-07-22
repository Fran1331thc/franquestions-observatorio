"""Entrada pública de FranQuestions para servicios de alojamiento de Streamlit."""

import os

os.environ.setdefault("FQ_ENV", "production")
os.environ.setdefault("FQ_API_URL", "http://127.0.0.1:9")

from fq_observatorio.dashboard import *  # noqa: F401,F403,E402
