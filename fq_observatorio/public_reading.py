"""Contrato interno para una futura lectura pública verificable.

Este módulo no concede permisos ni renderiza interfaz. Construye una salida
estructurada que puede validarse antes de considerar su exposición pública.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from urllib.parse import urlparse

from .intelligence import build_fq_reading


SCHEMA_VERSION = "public-reading/0.1-draft"


@dataclass(frozen=True)
class PublicSource:
    institution: str
    url: str
    consulted_on: date


@dataclass(frozen=True)
class ConfidenceStatement:
    claim: str
    level: str
    reasons: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PublicReading:
    schema_version: str
    generated_at: datetime
    indicator_slug: str
    claim: str
    evidence_class: str
    evidence_scope: str
    sources: tuple[PublicSource, ...]
    corroboration_status: str
    descriptive_reading: str
    mechanisms: tuple[str, ...]
    causal_magnitude_status: str
    sufficiency_status: str
    confidence: tuple[ConfidenceStatement, ...]
    trace: tuple[str, ...]
    remaining_uncertainty: str
    revision_condition: str
    status: str
    blocking_reasons: tuple[str, ...]


def _is_verifiable_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme == "https" and bool(parsed.netloc)


def build_public_reading(
    *,
    slug: str,
    name: str,
    unit: str,
    source: str,
    source_url: str,
    analysis: dict,
    caveat: str = "",
    consulted_on: date | None = None,
    generated_at: datetime | None = None,
) -> PublicReading:
    """Construye una lectura descriptiva; una traza incompleta bloquea su publicación."""
    consulted_on = consulted_on or date.today()
    generated_at = generated_at or datetime.now(timezone.utc)
    reading = build_fq_reading(slug, name, analysis, caveat)

    blocking_reasons: list[str] = []
    if not source.strip():
        blocking_reasons.append("La institución fuente no está identificada.")
    if not _is_verifiable_url(source_url):
        blocking_reasons.append("La fuente no tiene un enlace HTTPS verificable.")
    if not analysis.get("latest_period"):
        blocking_reasons.append("La observación no tiene un período identificable.")
    if analysis.get("latest_value") is None:
        blocking_reasons.append("La observación no tiene un valor identificable.")

    period = analysis.get("latest_period")
    value = analysis.get("latest_value")
    claim = reading["fact"]
    trace = (
        f"Fuente: {source or 'no identificada'} ({source_url or 'sin enlace'}).",
        f"Observación: período={period}; valor={value}; unidad={unit}.",
        f"Transformación descriptiva: tendencia={analysis.get('trend', 'no disponible')}.",
        f"Afirmación: {claim}",
        f"Límite: {reading['caveat']}",
    )

    descriptive_reasons = ["La afirmación conserva valor, unidad y período."]
    if analysis.get("previous_period"):
        descriptive_reasons.append("La comparación identifica la observación anterior.")
    else:
        descriptive_reasons.append("No existe comparación anterior disponible.")

    confidence = (
        ConfidenceStatement(
            claim="Descripción del movimiento observado",
            level="sustentada" if not blocking_reasons else "no asignada",
            reasons=tuple(descriptive_reasons),
            limitations=(reading["caveat"],),
        ),
        ConfidenceStatement(
            claim="Explicación causal del movimiento",
            level="no determinada",
            reasons=("La serie describe el movimiento, pero no identifica una causa.",),
            limitations=("No hay estimación causal de magnitud ni suficiencia.",),
        ),
    )

    return PublicReading(
        schema_version=SCHEMA_VERSION,
        generated_at=generated_at,
        indicator_slug=slug,
        claim=claim,
        evidence_class="serie oficial descriptiva/observacional",
        evidence_scope="describe valores y comparaciones; no identifica causalidad",
        sources=(PublicSource(source, source_url, consulted_on),) if source.strip() else (),
        corroboration_status="single_source" if source.strip() else "not_attempted",
        descriptive_reading=reading["meaning"],
        mechanisms=tuple(reading["hypotheses"]),
        causal_magnitude_status="not_estimated",
        sufficiency_status="not_demonstrated",
        confidence=confidence,
        trace=trace,
        remaining_uncertainty=reading["remaining_uncertainty"],
        revision_condition=reading["revision_condition"],
        status="blocked" if blocking_reasons else "complete",
        blocking_reasons=tuple(blocking_reasons),
    )


def validate_public_reading(reading: PublicReading) -> None:
    """Hace fallar una lectura que contradiga las invariantes del contrato."""
    if reading.status not in {"complete", "limited", "blocked", "superseded"}:
        raise ValueError("Estado público desconocido")
    if reading.status == "complete" and reading.blocking_reasons:
        raise ValueError("Una lectura completa no puede conservar bloqueos")
    if reading.status == "blocked" and not reading.blocking_reasons:
        raise ValueError("Una lectura bloqueada debe explicar el motivo")
    if reading.status == "complete" and (not reading.sources or len(reading.trace) < 5):
        raise ValueError("Una lectura completa requiere fuente y traza")
    if reading.causal_magnitude_status != "not_estimated":
        raise ValueError("La beta no autoriza estimaciones causales")
    if reading.sufficiency_status != "not_demonstrated":
        raise ValueError("La beta no autoriza suficiencia causal")
