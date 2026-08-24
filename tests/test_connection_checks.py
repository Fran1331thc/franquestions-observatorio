import unittest
from datetime import date

from fq_observatorio.connection_checks import check_bccr_connection
from fq_observatorio.connectors.base import ConnectorError, CredentialsError


class FakeConnector:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def fetch(self, code, start, end):
        self.call = (code, start, end)
        if self.error:
            raise self.error
        return self.result


class ConnectionCheckTests(unittest.TestCase):
    def test_success_does_not_require_persistence(self):
        connector = FakeConnector(
            result=[{"period": date(2026, 8, 1), "value": 500}]
        )
        result = check_bccr_connection(connector, today=date(2026, 8, 1))
        self.assertTrue(result.ok)
        self.assertEqual(result.observations, 1)
        self.assertEqual(connector.call[0], "318")

    def test_missing_credentials_are_explained(self):
        connector = FakeConnector(error=CredentialsError("faltan credenciales"))
        result = check_bccr_connection(connector, today=date(2026, 8, 1))
        self.assertFalse(result.ok)
        self.assertFalse(result.configured)

    def test_service_error_is_distinct_from_missing_configuration(self):
        connector = FakeConnector(error=ConnectorError("respuesta invalida"))
        result = check_bccr_connection(connector, today=date(2026, 8, 1))
        self.assertFalse(result.ok)
        self.assertTrue(result.configured)


if __name__ == "__main__":
    unittest.main()
