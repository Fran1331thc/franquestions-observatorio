class ConnectorError(RuntimeError):
    """Error recuperable al consultar o interpretar una fuente oficial."""


class CredentialsError(ConnectorError):
    """La fuente requiere configuracion o credenciales ausentes."""

