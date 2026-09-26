"""Planes seguros de actualizacion para todo el catalogo FranQuestions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .catalog import CATALOG
from .models import Observation, Series

OVERLAP_DAYS = {
    "daily": 7,
    "monthly": 62,
    "quarterly": 100,
    "annual": 400,
}

MANUAL_REQUIREMENTS = {
    "policy-rate": "1 archivo XLSX del BCCR",
    "inflation": "1 archivo XLSX del BCCR/INEC",
    "imae": "1 archivo XLSX del BCCR",
    "unemployment": "1 archivo XLSX de la ECE",
    "poverty": "1 archivo XLSX de ENAHO",
    "fiscal-balance": "1 archivo XLSX de Hacienda",
    "public-debt": "2 archivos XLSX: deuda y cifras fiscales para el PIB",
    "reserves": "1 archivo XLSX del BCCR",
    "exports": "1 archivo XLS exportado del cuadro oficial",
    "tourism": "1 informe PDF mensual del ICT",
    "fdi": "1 archivo XLS exportado del cuadro oficial",
}

UPDATE_MODES = {
    "exchange-rate": "Automatica supervisada",
    "policy-rate": "Semiautomatica",
    "inflation": "Semiautomatica",
    "imae": "Semiautomatica",
    "unemployment": "Semiautomatica",
    "poverty": "Semiautomatica",
    "fiscal-balance": "Semiautomatica",
    "public-debt": "Semiautomatica",
    "reserves": "Semiautomatica",
    "exports": "Semiautomatica",
    "tourism": "Semiautomatica",
    "fdi": "Semiautomatica",
}

HUMAN_ROLES = {
    "exchange-rate": "Confirmar la ejecucion y revisar el reporte",
    "public-debt": "Descargar 2 archivos, revisar la vista previa y confirmar",
}

DEFAULT_HUMAN_ROLE = "Descargar el archivo oficial, revisar la vista previa y confirmar"


@dataclass(frozen=True)
class IndicatorUpdatePlan:
    slug: str
    indicator: str
    latest_stored: date | None
    start: date
    end: date
    observation_frequency: str
    update_mode: str
    mechanism: str
    readiness: str
    requirement: str
    human_role: str
    next_action: str
    writes_require_confirmation: bool = True

    def as_dict(self) -> dict:
        result = asdict(self)
        for key in ("latest_stored", "start", "end"):
            value = result[key]
            result[key] = value.isoformat() if value else None
        return result


def build_all_update_plans(
    session: Session,
    *,
    today: date | None = None,
    bccr_credentials_ready: bool = False,
) -> list[IndicatorUpdatePlan]:
    """Construye planes sin consultar fuentes ni escribir observaciones."""
    end = today or date.today()
    series_by_slug = {
        item.slug: item for item in session.scalars(select(Series)).all()
    }
    plans = []
    for slug, catalog_item in CATALOG.items():
        series = series_by_slug.get(slug)
        latest = None
        if series:
            latest = session.scalar(
                select(func.max(Observation.period)).where(
                    Observation.series_id == series.id
                )
            )
        frequency = catalog_item.observation_frequency or catalog_item.frequency
        overlap = OVERLAP_DAYS[frequency]
        start = latest - timedelta(days=overlap) if latest else end - timedelta(days=365)
        if start > end:
            start = end

        if slug == "exchange-rate":
            mechanism = "API SDDE del BCCR"
            readiness = "Listo" if bccr_credentials_ready else "Esperando credenciales"
            requirement = "Token generado en Mi perfil del BCCR"
            next_action = (
                "Ejecutar la consulta y revisar el reporte"
                if bccr_credentials_ready
                else "Registrar la cuenta y configurar el token del BCCR"
            )
        else:
            mechanism = "Archivo oficial con vista previa"
            readiness = "Disponible con revision humana"
            requirement = MANUAL_REQUIREMENTS[slug]
            next_action = f"Descargar y cargar {requirement.lower()}"

        plans.append(
            IndicatorUpdatePlan(
                slug=slug,
                indicator=catalog_item.name,
                latest_stored=latest,
                start=start,
                end=end,
                observation_frequency=frequency,
                update_mode=UPDATE_MODES[slug],
                mechanism=mechanism,
                readiness=readiness,
                requirement=requirement,
                human_role=HUMAN_ROLES.get(slug, DEFAULT_HUMAN_ROLE),
                next_action=next_action,
            )
        )
    return plans


def summarize_update_modes(plans: list[IndicatorUpdatePlan]) -> dict[str, int]:
    """Resume el reparto operativo sin consultar fuentes ni modificar datos."""
    summary = {
        "Automatica supervisada": 0,
        "Semiautomatica": 0,
        "Manual": 0,
    }
    for plan in plans:
        summary[plan.update_mode] = summary.get(plan.update_mode, 0) + 1
    return summary
