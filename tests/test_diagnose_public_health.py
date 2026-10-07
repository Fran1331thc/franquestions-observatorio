import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripts.diagnose_public_health import probe, sanitize_url


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ok":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        elif self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"bad request")

    def log_message(self, format, *args):  # noqa: A003
        pass


class PublicHealthDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), HealthHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_ok_response_passes(self):
        result = probe(f"{self.base_url}/ok", timeout=2, max_redirects=2)
        self.assertEqual("pass", result["result"])
        self.assertEqual(200, result["http_status"])
        self.assertEqual("ok", result["body_excerpt"])
        self.assertEqual(0, result["redirect_count"])

    def test_redirect_is_recorded(self):
        result = probe(f"{self.base_url}/redirect", timeout=2, max_redirects=2)
        self.assertEqual("pass", result["result"])
        self.assertEqual(1, result["redirect_count"])

    def test_query_values_are_redacted(self):
        safe = sanitize_url("https://example.test/login?payload=secret&next=/app#fragment")
        self.assertEqual(
            "https://example.test/login?payload=<redacted>&next=<redacted>", safe
        )


if __name__ == "__main__":
    unittest.main()
