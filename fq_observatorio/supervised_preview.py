"""Vista previa y puerta de seguridad para actualizaciones supervisadas."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Iterable

from .shadow_audit import independent_successful_days, verify_shadow_audit


@dataclass(frozen=True)
class ReadinessGate:
    ready: bool
    successful_days: int
    required_days: int
    chain_valid: bool
    current_check_passed: bool
    read_only_history: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["reasons"] = list(self.reasons)
        return result


def evaluate_readiness(
    records: Iterable[dict[str, Any]],
    *,
    current_check_passed: bool,
    current_writes_performed: bool = False,
    required_days: int = 3,
) -> ReadinessGate:
    """Evalúa condiciones independientes de la interfaz y de cualquier escritura."""
    history = list(records)
    chain_valid = verify_shadow_audit(history)
    successful_days = independent_successful_days(history)
    read_only_history = all(record.get("writes_performed") is False for record in history)
    reasons: list[str] = []
    if not chain_valid:
        reasons.append("La cadena de integridad del historial no es válida.")
    if successful_days < required_days:
        missing = required_days - successful_days
        reasons.append(f"Faltan {missing} día(s) satisfactorio(s) e independiente(s).")
    if not current_check_passed:
        reasons.append("La comprobación actual no superó todas las validaciones.")
    if current_writes_performed or not read_only_history:
        reasons.append("El historial debe contener exclusivamente pruebas de solo lectura.")
    return ReadinessGate(
        ready=not reasons,
        successful_days=successful_days,
        required_days=required_days,
        chain_valid=chain_valid,
        current_check_passed=current_check_passed,
        read_only_history=read_only_history and not current_writes_performed,
        reasons=tuple(reasons),
    )


def build_human_review_checklist(preview: dict[str, Any]) -> list[dict[str, str]]:
    """Traduce las salvaguardas técnicas en verificaciones comprensibles."""
    gate = preview["gate"]
    candidates = preview.get("candidates", [])
    revisions = sum(row.get("Acción") == "Revisar" for row in candidates)
    return [
        {
            "Comprobación": "Historial íntegro",
            "Estado": "Cumple" if gate["chain_valid"] else "Bloquea",
            "Evidencia": "Cadena criptográfica verificada"
            if gate["chain_valid"]
            else "La cadena no supera la verificación",
        },
        {
            "Comprobación": "Repetición independiente",
            "Estado": "Cumple"
            if gate["successful_days"] >= gate["required_days"]
            else "Pendiente",
            "Evidencia": (
                f"{gate['successful_days']}/{gate['required_days']} días satisfactorios"
            ),
        },
        {
            "Comprobación": "Validación actual",
            "Estado": "Cumple" if preview["errors"] == 0 else "Bloquea",
            "Evidencia": f"{preview['errors']} errores; {preview['warnings']} advertencias",
        },
        {
            "Comprobación": "Prueba sin escritura",
            "Estado": "Cumple"
            if gate["read_only_history"] and not preview["writes_performed"]
            else "Bloquea",
            "Evidencia": "0 escrituras realizadas"
            if not preview["writes_performed"]
            else "Se detectaron escrituras",
        },
        {
            "Comprobación": "Revisiones de valores existentes",
            "Estado": "Cumple" if revisions == 0 else "Revisión humana",
            "Evidencia": f"{revisions} valores publicados cambiarían",
        },
        {
            "Comprobación": "Autorización humana final",
            "Estado": "No solicitada",
            "Evidencia": "No existe un control para aplicar cambios en esta etapa",
        },
    ]


def build_supervised_preview(
    session: Any,
    *,
    start: date,
    end: date,
    audit_records: Iterable[dict[str, Any]],
    connector: Any,
    slug: str = "exchange-rate",
    indicator_code: str = "318",
) -> dict[str, Any]:
    """Consulta y compara candidatos sin flush, commit ni modificación de modelos."""
    from sqlalchemy import select

    from .manual_import import compare_rows
    from .models import Series
    from .validation import ValidationIssue, validate_series

    if start > end:
        raise ValueError("La fecha inicial no puede ser posterior a la final")
    series = session.scalar(select(Series).where(Series.slug == slug))
    if not series:
        raise ValueError(f"Serie desconocida: {slug}")

    rows = connector.fetch(indicator_code, start, end)
    issues = validate_series(rows, series.frequency)
    for row in rows:
        period = row.get("period")
        if isinstance(period, date) and period > end:
            issues.append(
                ValidationIssue(
                    "future_period",
                    "error",
                    "Periodo posterior al límite solicitado",
                    period,
                )
            )
    comparison = compare_rows(session, slug, rows)
    errors = sum(issue.severity == "error" for issue in issues)
    gate = evaluate_readiness(
        audit_records,
        current_check_passed=bool(rows) and errors == 0,
        current_writes_performed=False,
    )

    candidates = [
        {
            "Acción": "Agregar",
            "Fecha": row["period"].isoformat(),
            "Valor publicado": None,
            "Valor propuesto": float(row["value"]),
        }
        for row in comparison.new_rows
    ]
    candidates.extend(
        {
            "Acción": "Revisar",
            "Fecha": row["period"].isoformat(),
            "Valor publicado": float(row["current_value"]),
            "Valor propuesto": float(row["file_value"]),
        }
        for row in comparison.revised_rows
    )
    candidates.sort(key=lambda row: row["Fecha"], reverse=True)
    preview = {
        "source": "BCCR",
        "indicator_code": indicator_code,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "rows_received": len(rows),
        "unchanged": comparison.unchanged,
        "errors": errors,
        "warnings": sum(issue.severity == "warning" for issue in issues),
        "database_latest": comparison.database_latest.isoformat()
        if comparison.database_latest
        else None,
        "source_latest": comparison.file_latest.isoformat()
        if comparison.file_latest
        else None,
        "candidates": candidates,
        "gate": gate.as_dict(),
        "writes_performed": False,
    }
    preview["review_checklist"] = build_human_review_checklist(preview)
    return preview
