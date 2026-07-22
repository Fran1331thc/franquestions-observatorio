from dataclasses import asdict, dataclass
from datetime import date


FREQUENCY_MAX_DAYS = {"daily": 5, "monthly": 45, "quarterly": 120, "annual": 400, "event": None}


@dataclass
class ValidationIssue:
    kind: str
    severity: str
    message: str
    period: date | None = None


def validate_series(rows: list[dict], frequency: str, extreme_pct: float = 50.0) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    periods = [row.get("period") for row in rows]
    valid_dates = []
    for period in periods:
        if not isinstance(period, date):
            issues.append(ValidationIssue("invalid_date", "error", f"Fecha invalida: {period!r}"))
        else:
            valid_dates.append(period)
    duplicates = {p for p in valid_dates if valid_dates.count(p) > 1}
    for period in sorted(duplicates):
        issues.append(ValidationIssue("duplicate", "error", "Periodo duplicado", period))
    for row in rows:
        if row.get("value") is None:
            issues.append(ValidationIssue("missing", "error", "Valor faltante", row.get("period")))

    ordered = sorted((row for row in rows if isinstance(row.get("period"), date) and row.get("value") is not None), key=lambda r: r["period"])
    max_days = FREQUENCY_MAX_DAYS.get(frequency)
    if max_days:
        for previous, current in zip(ordered, ordered[1:]):
            gap = (current["period"] - previous["period"]).days
            if gap > max_days:
                issues.append(ValidationIssue("frequency_gap", "warning", f"Brecha de {gap} dias; frecuencia esperada {frequency}", current["period"]))
    changes = []
    for previous, current in zip(ordered, ordered[1:]):
        base = abs(float(previous["value"]))
        if base:
            changes.append((abs((float(current["value"]) - float(previous["value"])) / base) * 100, current["period"]))
    for change, period in changes:
        if change > extreme_pct:
            issues.append(ValidationIssue("extreme_change", "warning", f"Cambio extremo de {change:.1f}%", period))
    return issues


def issues_as_dicts(issues: list[ValidationIssue]) -> list[dict]:
    return [asdict(issue) for issue in issues]
