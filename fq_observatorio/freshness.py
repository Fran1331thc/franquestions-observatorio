"""Reglas transparentes para evaluar la vigencia de las series."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta


FRESHNESS_WINDOWS = {
    "daily": (4, 10),
    "monthly": (62, 100),
    "quarterly": (155, 220),
    "annual": (430, 550),
}

OFFICIAL_RELEASE_GRACE_DAYS = 3


def _next_official_release(slug: str, latest_period: date) -> date | None:
    """Return the first official release that can update the loaded period."""
    if slug == "exchange-rate":
        return None
    try:
        from .publication_calendar import OFFICIAL_RELEASES_2026
    except ImportError:
        return None
    releases = OFFICIAL_RELEASES_2026.get(slug, [])
    future = [release[0] for release in releases if release[0] > latest_period]
    return min(future) if future else None


@dataclass(frozen=True)
class FreshnessStatus:
    slug: str
    latest_period: date
    as_of: date
    age_days: int
    review_due: date
    status: str
    label: str
    severity: str
    explanation: str

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_freshness(
    slug: str,
    latest_period: date,
    frequency: str,
    as_of: date | None = None,
    use_official_schedule: bool = True,
) -> FreshnessStatus:
    """Classify a series using documented frequency-specific age windows."""
    reference_date = as_of or date.today()
    age_days = max(0, (reference_date - latest_period).days)
    fresh_days, warning_days = FRESHNESS_WINDOWS.get(frequency, (62, 100))

    official_due = _next_official_release(slug, latest_period) if use_official_schedule else None
    if official_due:
        if reference_date < official_due:
            status, label, severity = "current", "Al día", "info"
            explanation = "La próxima publicación figura en el calendario oficial y todavía no ha vencido."
        elif reference_date <= official_due + timedelta(days=OFFICIAL_RELEASE_GRACE_DAYS):
            status, label, severity = "review", "Revisar fuente oficial", "warning"
            explanation = "La fecha oficial de publicación ya llegó; conviene comprobar si existe un dato nuevo."
        else:
            status, label, severity = "overdue", "Actualización pendiente", "error"
            explanation = "La fecha oficial de publicación venció y todavía no se ha incorporado un dato nuevo."

        return FreshnessStatus(
            slug=slug,
            latest_period=latest_period,
            as_of=reference_date,
            age_days=age_days,
            review_due=official_due,
            status=status,
            label=label,
            severity=severity,
            explanation=explanation,
        )

    if age_days <= fresh_days:
        status, label, severity = "current", "Al día", "info"
        explanation = "La última observación está dentro del plazo esperado para su frecuencia."
    elif age_days <= warning_days:
        status, label, severity = "review", "Revisar pronto", "warning"
        explanation = "La serie se acerca al límite esperado; conviene revisar la fuente oficial."
    else:
        status, label, severity = "overdue", "Actualización pendiente", "error"
        explanation = "La última observación supera el plazo esperado para su frecuencia."

    return FreshnessStatus(
        slug=slug,
        latest_period=latest_period,
        as_of=reference_date,
        age_days=age_days,
        review_due=latest_period + timedelta(days=fresh_days),
        status=status,
        label=label,
        severity=severity,
        explanation=explanation,
    )


def apply_source_check(status: dict, checked_on: date | None, frequency: str) -> dict:
    """Acknowledge that an official source was checked but had no newer value."""
    if not checked_on or status.get("status") not in {"review", "overdue"}:
        return status
    review_due = status.get("review_due")
    if review_due and checked_on < review_due:
        return status
    fresh_days, _ = FRESHNESS_WINDOWS.get(frequency, (62, 100))
    return {
        **status,
        "status": "checked",
        "label": "Fuente revisada, sin dato nuevo",
        "severity": "info",
        "last_checked": checked_on,
        "review_due": checked_on + timedelta(days=fresh_days),
        "explanation": "La fuente oficial fue revisada y todavía no publicó una observación posterior.",
    }
