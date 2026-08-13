import io
import logging
from decimal import Decimal, InvalidOperation

import httpx
import pandas as pd

from ..config import Settings, get_settings
from .base import ConnectorError, CredentialsError

logger = logging.getLogger(__name__)


class INECConnector:
    """Conector generico para archivos CSV oficiales publicados por INEC.

    La URL y los nombres de columnas se parametrizan porque los productos de INEC
    no comparten un contrato tabular unico.
    """

    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None):
        self.settings = settings or get_settings()
        self.client = client or httpx.Client(timeout=self.settings.http_timeout_seconds)

    def fetch(self, url: str | None = None, date_column: str = "period", value_column: str = "value") -> list[dict]:
        target = url or self.settings.inec_data_url
        if not target:
            raise CredentialsError("Configure FQ_INEC_DATA_URL con un CSV oficial de INEC")
        try:
            response = self.client.get(target)
            response.raise_for_status()
            frame = pd.read_csv(io.BytesIO(response.content))
        except (httpx.HTTPError, pd.errors.ParserError) as exc:
            logger.exception("Fallo al descargar datos INEC")
            raise ConnectorError(f"No se pudo leer el recurso INEC: {exc}") from exc
        return self.parse_frame(frame, date_column, value_column)

    @staticmethod
    def parse_frame(frame: pd.DataFrame, date_column: str, value_column: str) -> list[dict]:
        missing = {date_column, value_column} - set(frame.columns)
        if missing:
            raise ConnectorError(f"Columnas INEC ausentes: {', '.join(sorted(missing))}")
        rows = []
        for _, row in frame.iterrows():
            try:
                period = pd.to_datetime(row[date_column], errors="raise").date()
                value = Decimal(str(row[value_column]).replace(",", ""))
            except (ValueError, TypeError, InvalidOperation) as exc:
                raise ConnectorError(f"Fila INEC invalida: {row.to_dict()}") from exc
            rows.append({"period": period, "value": value})
        return rows
