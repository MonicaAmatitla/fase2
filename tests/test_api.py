import io
import json
import sys
import unittest
from pathlib import Path
from wsgiref.util import setup_testing_defaults

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from server import application


def request(method, path, payload=None, content_type="application/json", raw_body=None):
    body = raw_body if raw_body is not None else json.dumps(payload).encode() if payload is not None else b""
    environ = {}
    setup_testing_defaults(environ)
    environ.update({"REQUEST_METHOD": method, "PATH_INFO": path, "CONTENT_LENGTH": str(len(body)),
                   "CONTENT_TYPE": content_type, "wsgi.input": io.BytesIO(body)})
    captured = {}
    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)
    result = b"".join(application(environ, start_response))
    captured["body"] = result
    return captured


class ApiTests(unittest.TestCase):
    def test_health(self):
        response = request("GET", "/health")
        self.assertTrue(response["status"].startswith("200"))
        self.assertEqual(json.loads(response["body"])["status"], "ok")

    def test_frontend(self):
        response = request("GET", "/")
        self.assertTrue(response["status"].startswith("200"))
        self.assertIn(b"/api/predict", response["body"])

    def test_prediction(self):
        response = request("POST", "/api/predict", {"text": "El resultado fue excelente"})
        self.assertTrue(response["status"].startswith("200"))
        self.assertIn("prediction", json.loads(response["body"]))

    def test_rejects_empty_text(self):
        response = request("POST", "/api/predict", {"text": " "})
        self.assertTrue(response["status"].startswith("400"))

    def test_rejects_wrong_content_type(self):
        response = request("POST", "/api/predict", {"text": "hola"}, "text/plain")
        self.assertTrue(response["status"].startswith("415"))

    def test_rejects_invalid_json(self):
        response = request("POST", "/api/predict", raw_body=b"{")
        self.assertTrue(response["status"].startswith("400"))

    def test_rejects_oversized_text(self):
        response = request("POST", "/api/predict", {"text": "x" * 4001})
        self.assertTrue(response["status"].startswith("400"))

    def test_not_found(self):
        response = request("GET", "/missing")
        self.assertTrue(response["status"].startswith("404"))


if __name__ == "__main__":
    unittest.main()
