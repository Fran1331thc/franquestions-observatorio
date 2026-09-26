"""Evaluacion conservadora para ampliar la automatizacion de indicadores."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AutomationCandidate:
    slug: str
    indicator: str
    priority: str
    official_source: bool
    machine_endpoint_verified: bool
    official_series_code_verified: bool
    candidate_series_code: str | None
    code_evidence: str
    parser_available: bool
    validation_available: bool
    shadow_runs_required: int
    next_experiment: str

    @property
    def ready_for_supervised_automation(self) -> bool:
        """Solo autoriza el ascenso cuando todas las barreras estan verificadas."""
        return all(
            (
                self.official_source,
                self.machine_endpoint_verified,
                self.official_series_code_verified,
                self.parser_available,
                self.validation_available,
            )
        ) and self.shadow_runs_required == 0

    def as_dict(self) -> dict:
        result = asdict(self)
        result["ready_for_supervised_automation"] = (
            self.ready_for_supervised_automation
        )
        return result


def priority_automation_candidates() -> list[AutomationCandidate]:
    """Devuelve la primera cola de investigacion sin consultar ni escribir datos."""
    common = {
        "priority": "Alta",
        "official_source": True,
        "machine_endpoint_verified": False,
        "official_series_code_verified": False,
        "parser_available": True,
        "validation_available": True,
        "shadow_runs_required": 3,
    }
    return [
        AutomationCandidate(
            slug="policy-rate",
            indicator="Tasa de Politica Monetaria",
            candidate_series_code="3541",
            code_evidence=(
                "Codigo provisional documentado por una biblioteca tecnica; "
                "pendiente de corroboracion en el catalogo oficial del BCCR"
            ),
            next_experiment=(
                "Confirmar el codigo oficial de la serie BCCR y ejecutar tres "
                "consultas sin escritura contra el archivo vigente"
            ),
            **common,
        ),
        AutomationCandidate(
            slug="reserves",
            indicator="Reservas brutas del Banco Central",
            candidate_series_code=None,
            code_evidence="Pendiente de localizar en el catalogo oficial del BCCR",
            next_experiment=(
                "Confirmar el codigo oficial de la serie BCCR y ejecutar tres "
                "consultas sin escritura contra el archivo vigente"
            ),
            **common,
        ),
    ]
