import unittest
from decimal import Decimal

from fq_observatorio.connectors.bccr import BCCRConnector


class BCCRConnectorTests(unittest.TestCase):
    def test_parses_iso_and_day_first_dates(self):
        raw = """
        <DATOS>
          <INGC011_CAT_INDICADORECONOMIC><DES_FECHA>2026-08-01</DES_FECHA><NUM_VALOR>452.51</NUM_VALOR></INGC011_CAT_INDICADORECONOMIC>
          <INGC011_CAT_INDICADORECONOMIC><DES_FECHA>02/08/2026 00:00:00</DES_FECHA><NUM_VALOR>453,25</NUM_VALOR></INGC011_CAT_INDICADORECONOMIC>
        </DATOS>
        """
        rows = BCCRConnector.parse(raw)
        self.assertEqual(rows[0]["period"].isoformat(), "2026-08-01")
        self.assertEqual(rows[1]["period"].isoformat(), "2026-08-02")
        self.assertEqual(rows[0]["value"], Decimal("452.51"))
        self.assertEqual(rows[1]["value"], Decimal("453.25"))

    def test_parses_escaped_xml_wrapper(self):
        raw = """<string>&lt;DATOS&gt;&lt;ROW&gt;&lt;DES_FECHA&gt;01/08/2026&lt;/DES_FECHA&gt;&lt;NUM_VALOR&gt;1.234,56&lt;/NUM_VALOR&gt;&lt;/ROW&gt;&lt;/DATOS&gt;</string>"""
        rows = BCCRConnector.parse(raw)
        self.assertEqual(rows[0]["value"], Decimal("1234.56"))


if __name__ == "__main__":
    unittest.main()
