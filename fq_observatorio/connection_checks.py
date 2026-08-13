"""Comprobaciones de conectividad que nunca escriben datos economicos."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta

from .connectors import BCCRConnector
from .connectors.base import ConnectorError, CredentialsError


@dataclass(frozen=True)
class ConnectionCheck:
    service: str
    ok: bool
    configured: bool
    observations: int
    latest_period: str | None
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


def check_bccr_connection(
    connector: BCCRConnector | None = None,
    *,
    today: date | None = None,
) -> ConnectionCheck:
    """Prueba el codigo 318 en una ventana corta, sin persistir resultados."""
    client = connector or BCCRConnector()
    end = today or date.today()
    start = end - timedelta(days=10)
    try:
        rows = client.fetch("318", start, end)
    except CredentialsError as exc:
        return ConnectionCheck(
            service="BCCR",
            ok=False,
            configured=False,
            observations=0,
            latest_period=None,
            message=str(exc),
        )
    except ConnectorError as exc:
        return ConnectionCheck(
            service="BCCR",
            ok=False,
            configured=True,
            observations=0,
            latest_period=None,
            message=str(exc),
        )
    except Exception as exc:
        return ConnectionCheck(
            service="BCCR",
            ok=False,
            configured=True,
            observations=0,
            latest_period=None,
            message=f"Fallo inesperado al probar BCCR: {exc}",
        )

    latest = max(row["period"] for row in rows) if rows else None
    return ConnectionCheck(
        service="BCCR",
        ok=bool(rows),
        configured=True,
        observations=len(rows),
        latest_period=latest.isoformat() if latest else None,
        message=(
            "Conexion y lectura de muestra correctas. Ningun dato fue guardado."
            if rows
            else "La conexion respondio, pero no devolvio observaciones en la ventana de prueba."
        ),
    )
