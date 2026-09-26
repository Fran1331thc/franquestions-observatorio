import json
import logging
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import httpx

from ..config import Settings, get_settings
from .base import ConnectorError, CredentialsError

logger = logging.getLogger(__name__)


class BCCRConnector:
    def __init__(self, settings: Settings | None = None, client: httpx.Client | None = None):
        self.settings = settings or get_settings()
        self.client = client or httpx.Client(timeout=self.settings.http_timeout_seconds)

    def fetch(self, indicator_code: str, start: date, end: date) -> list[dict]:
        if not self.settings.bccr_token:
            raise CredentialsError("BCCR requiere FQ_BCCR_TOKEN")
        url = (
            f"{self.settings.bccr_base_url.rstrip('/')}"
            f"/indicadoresEconomicos/{indicator_code}/series"
        )
        params = {
            "fechaInicio": start.strftime("%Y/%m/%d"),
            "fechaFin": end.strftime("%Y/%m/%d"),
            "idioma": "ES",
        }
        headers = {
            "Authorization": f"Bearer {self.settings.bccr_token}",
            "Accept": "application/json",
        }
        try:
            response = self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return self.parse_json(response.json())
        except httpx.HTTPError as exc:
            logger.exception("Fallo HTTP al consultar BCCR", extra={"indicator": indicator_code})
            raise ConnectorError(f"No se pudo consultar BCCR: {exc}") from exc

    @staticmethod
    def parse_json(payload: dict | str) -> list[dict]:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ConnectorError("BCCR devolvio JSON invalido") from exc
        if not isinstance(payload, dict) or payload.get("estado") is False:
            message = (
                payload.get("mensaje", "respuesta no reconocida")
                if isinstance(payload, dict)
                else "respuesta no reconocida"
            )
            raise ConnectorError(f"BCCR no completo la consulta: {message}")

        rows = []
        for indicator in payload.get("datos", []):
            for item in indicator.get("series", []):
                raw_date = str(item.get("fecha", ""))
                raw_value = item.get("valorDatoPorPeriodo")
                if not raw_date or raw_value is None:
                    continue
                try:
                    rows.append(
                        {
                            "period": BCCRConnector._parse_date(raw_date),
                            "value": BCCRConnector._parse_value(str(raw_value)),
                        }
                    )
                except (ValueError, InvalidOperation) as exc:
                    raise ConnectorError(
                        f"Fila BCCR invalida: fecha={raw_date}, valor={raw_value}"
                    ) from exc
        if not rows:
            raise ConnectorError("La respuesta BCCR no contiene observaciones reconocibles")
        return rows

    @staticmethod
    def _parse_date(raw_date: str) -> date:
        candidate = raw_date.strip()[:10]
        for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(candidate, pattern).date()
            except ValueError:
                continue
        raise ValueError(f"Fecha BCCR no reconocida: {raw_date}")

    @staticmethod
    def _parse_value(raw_value: str) -> Decimal:
        candidate = raw_value.strip().replace(" ", "")
        if "," in candidate and "." in candidate:
            if candidate.rfind(",") > candidate.rfind("."):
                candidate = candidate.replace(".", "").replace(",", ".")
            else:
                candidate = candidate.replace(",", "")
        elif "," in candidate:
            candidate = candidate.replace(",", ".")
        return Decimal(candidate)

    @staticmethod
    def parse(raw_xml: str) -> list[dict]:
        """Compatibilidad para validar respuestas archivadas del servicio anterior."""
        try:
            root = ET.fromstring(raw_xml)
            # El endpoint envuelve el XML de datos como texto escapado.
            if root.tag.endswith("string") and root.text and "<" in root.text:
                root = ET.fromstring(root.text)
        except ET.ParseError as exc:
            raise ConnectorError("BCCR devolvio XML invalido") from exc

        rows = []
        for node in root.iter():
            children = {child.tag.split("}")[-1].upper(): (child.text or "").strip() for child in node}
            raw_date = children.get("DES_FECHA") or children.get("FECHA")
            raw_value = children.get("NUM_VALOR") or children.get("VALOR")
            if not raw_date or not raw_value:
                continue
            try:
                parsed_date = BCCRConnector._parse_date(raw_date)
                parsed_value = BCCRConnector._parse_value(raw_value)
            except (ValueError, InvalidOperation) as exc:
                raise ConnectorError(f"Fila BCCR invalida: fecha={raw_date}, valor={raw_value}") from exc
            rows.append({"period": parsed_date, "value": parsed_value})
        if not rows:
            raise ConnectorError("La respuesta BCCR no contiene observaciones reconocibles")
        return rows
