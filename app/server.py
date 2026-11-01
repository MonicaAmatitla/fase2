"""Small dependency-free WSGI API and static frontend server."""
import json
import os
from pathlib import Path
from wsgiref.simple_server import make_server

from model_adapter import IS_DEMO, predict

STATIC = Path(__file__).parent / "static"
MAX_BODY = 16_384


def respond(start_response, status, body, content_type="application/json; charset=utf-8"):
    raw = body if isinstance(body, bytes) else body.encode("utf-8")
    start_response(status, [("Content-Type", content_type), ("Content-Length", str(len(raw))),
                           ("X-Content-Type-Options", "nosniff"), ("Cache-Control", "no-store")])
    return [raw]


def application(environ, start_response):
    method, path = environ.get("REQUEST_METHOD", "GET"), environ.get("PATH_INFO", "/")
    if method == "GET" and path == "/health":
        return respond(start_response, "200 OK", json.dumps({"status": "ok", "demo": IS_DEMO}))
    if method == "GET" and path in ("/", "/index.html"):
        return respond(start_response, "200 OK", (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
    if method == "POST" and path == "/api/predict":
        try:
            length = int(environ.get("CONTENT_LENGTH") or "0")
            if length < 1 or length > MAX_BODY:
                return respond(start_response, "413 Content Too Large", json.dumps({"error": "Cuerpo vacío o mayor a 16 KB"}))
            if "application/json" not in environ.get("CONTENT_TYPE", ""):
                return respond(start_response, "415 Unsupported Media Type", json.dumps({"error": "Se requiere application/json"}))
            payload = json.loads(environ["wsgi.input"].read(length))
            text = payload.get("text") if isinstance(payload, dict) else None
            if not isinstance(text, str) or not text.strip():
                return respond(start_response, "400 Bad Request", json.dumps({"error": "El campo text es obligatorio"}))
            if len(text) > 4000:
                return respond(start_response, "400 Bad Request", json.dumps({"error": "text admite hasta 4000 caracteres"}))
            return respond(start_response, "200 OK", json.dumps(predict(text), ensure_ascii=False))
        except (ValueError, json.JSONDecodeError):
            return respond(start_response, "400 Bad Request", json.dumps({"error": "JSON inválido"}))
        except Exception:
            return respond(start_response, "500 Internal Server Error", json.dumps({"error": "No se pudo ejecutar la inferencia"}))
    return respond(start_response, "404 Not Found", json.dumps({"error": "No encontrado"}))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    with make_server("0.0.0.0", port, application) as httpd:
        print(f"Servidor listo en 0.0.0.0:{port}", flush=True)
        httpd.serve_forever()
