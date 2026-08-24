"""Pruebas de contrato para los 12 formatos oficiales del actualizador.

Las muestras son sintéticas, mínimas y se crean en una carpeta temporal. No
leen ni modifican la base vigente de FranQuestions.
"""

from __future__ import annotations

import tempfile
import unittest
from contextlib import nullcontext
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from fq_observatorio.updater import parse_upload


class OfficialFormatParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _xlsx(self, name: str, frame: pd.DataFrame, sheet: str, startrow: int = 0) -> Path:
        path = self.root / name
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            frame.to_excel(writer, sheet_name=sheet, index=False, startrow=startrow)
        return path

    def _raw_xlsx(self, name: str, rows: int, columns: int, sheet: str) -> tuple[Path, pd.DataFrame]:
        path = self.root / name
        frame = pd.DataFrame([[None] * columns for _ in range(rows)])
        return path, frame

    def _assert_single(self, rows: list[dict], period: date, value: str) -> None:
        self.assertEqual(rows, [{"period": period, "value": Decimal(value)}])

    def test_exchange_rate_format(self) -> None:
        path = self._xlsx("exchange.xlsx", pd.DataFrame({
            "Fecha": [date(2026, 8, 1)], "Tipo cambio venta": [501.25]
        }), "Sheet1", 4)
        self._assert_single(parse_upload("exchange-rate", path), date(2026, 8, 1), "501.25")

    def test_policy_rate_format(self) -> None:
        path = self._xlsx("policy.xlsx", pd.DataFrame({
            "Fecha": [date(2026, 7, 23)], "Tasa política monetaria": [3.25]
        }), "Sheet1", 4)
        self._assert_single(parse_upload("policy-rate", path), date(2026, 7, 23), "3.25")

    def test_inflation_format(self) -> None:
        path = self._xlsx("inflation.xlsx", pd.DataFrame({
            "Fecha": [date(2026, 7, 31)], "IPC, variación interanual (%)": [-0.52]
        }), "Sheet1", 4)
        self._assert_single(parse_upload("inflation", path), date(2026, 7, 31), "-0.52")

    def test_imae_format(self) -> None:
        path = self._xlsx("imae.xlsx", pd.DataFrame({
            "Fecha": [date(2026, 6, 30)], "IMAE, variación interanual (%)": [3.4]
        }), "Sheet1", 4)
        self._assert_single(parse_upload("imae", path), date(2026, 6, 30), "3.4")

    def test_reserves_format(self) -> None:
        path = self._xlsx("reserves.xlsx", pd.DataFrame({
            "Fecha": [date(2026, 7, 31)], "Reservas brutas del Banco Central": [20661.84]
        }), "Sheet1", 4)
        self._assert_single(parse_upload("reserves", path), date(2026, 7, 31), "20661.84")

    def test_unemployment_moving_quarter_format(self) -> None:
        path, frame = self._raw_xlsx("unemployment.xlsx", 110, 3, "C1 total ")
        frame.iloc[3, 1:] = ["EFM 2026", "FMA 2026"]
        frame.iloc[109, 1:] = [7.1, 6.8]
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            frame.to_excel(writer, sheet_name="C1 total ", index=False, header=False)
        rows = parse_upload("unemployment", path)
        self.assertEqual(rows, [
            {"period": date(2026, 3, 31), "value": Decimal("7.1")},
            {"period": date(2026, 4, 30), "value": Decimal("6.8")},
        ])

    def test_poverty_annual_format(self) -> None:
        path = self._xlsx("poverty.xlsx", pd.DataFrame({
            "Región de planificación y año": ["Total país 2025", "Central 2025"],
            "Total pobreza no extrema y pobreza extrema": [15.2, 12.0],
        }), "Cuadro 1", 2)
        self._assert_single(parse_upload("poverty", path), date(2025, 7, 31), "15.2")

    def test_fiscal_balance_annual_format_and_scale(self) -> None:
        path, frame = self._raw_xlsx("fiscal.xlsx", 78, 3, "ACUMULADO")
        frame.iloc[6, 1] = 2025
        frame.iloc[71, 1] = -0.0341
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            frame.to_excel(writer, sheet_name="ACUMULADO", index=False, header=False)
        self._assert_single(parse_upload("fiscal-balance", path), date(2025, 12, 31), "-3.4100")

    def test_public_debt_combines_balances_and_gdp(self) -> None:
        debt_path, debt = self._raw_xlsx("debt.xlsx", 12, 3, "Hoja1")
        debt.iloc[5, 1] = date(2025, 12, 31)
        debt.iloc[7, 1] = 400
        debt.iloc[11, 1] = 200
        with pd.ExcelWriter(debt_path, engine="openpyxl") as writer:
            debt.to_excel(writer, sheet_name="Hoja1", index=False, header=False)

        gdp_path, gdp = self._raw_xlsx("gdp.xlsx", 78, 3, "ACUMULADO")
        gdp.iloc[6, 1] = 2025
        gdp.iloc[77, 1] = 1000
        with pd.ExcelWriter(gdp_path, engine="openpyxl") as writer:
            gdp.to_excel(writer, sheet_name="ACUMULADO", index=False, header=False)
        self._assert_single(parse_upload("public-debt", debt_path, gdp_path), date(2025, 12, 31), "60.0")

    def test_exports_bccr_html_monthly_format(self) -> None:
        path = self.root / "exports.xls"
        path.write_text(
            "<table><tr><td>Mes</td><td>2025</td><td>2026</td></tr>"
            "<tr><td>Enero</td><td>100</td><td>120</td></tr>"
            "<tr><td>Total</td><td>100</td><td>120</td></tr></table>",
            encoding="windows-1252",
        )
        rows = parse_upload("exports", path)
        self.assertEqual(rows, [
            {"period": date(2025, 1, 31), "value": Decimal("100")},
            {"period": date(2026, 1, 31), "value": Decimal("120")},
        ])

    def test_tourism_ict_pdf_format(self) -> None:
        path = self.root / "tourism.pdf"
        path.write_bytes(b"%PDF synthetic fixture")
        text = "Cuadro 11\nMes 2025 2026\nEnero 123 456 234 567\nCuadro 12"
        page = type("Page", (), {"extract_text": lambda self: text})()
        document = type("Document", (), {"pages": [page] * 12})()
        with patch("pdfplumber.open", return_value=nullcontext(document)):
            rows = parse_upload("tourism", path)
        self.assertEqual(rows, [
            {"period": date(2025, 1, 31), "value": Decimal("123456")},
            {"period": date(2026, 1, 31), "value": Decimal("234567")},
        ])

    def test_fdi_bccr_html_quarterly_format(self) -> None:
        path = self.root / "fdi.xls"
        path.write_text(
            "<table><tr><td>Concepto</td><td>Trimestre 4/2025</td><td>Trimestre 1/2026</td></tr>"
            "<tr><td>Total Inversion directa en la economia declarante</td>"
            "<td>1500</td><td>1700</td></tr></table>",
            encoding="windows-1252",
        )
        rows = parse_upload("fdi", path)
        self.assertEqual(rows, [
            {"period": date(2025, 12, 31), "value": Decimal("1500")},
            {"period": date(2026, 3, 31), "value": Decimal("1700")},
        ])


if __name__ == "__main__":
    unittest.main()
