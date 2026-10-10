"""HTTP adapter over the classifier nucleus: validate, delegate, serialize."""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from math import isfinite

from classifier import classify


def _extract_views(body):
    views = body.get("views") if isinstance(body, dict) else None
    if not isinstance(views, list) or not 24 <= len(views) <= 168:
        raise ValueError("views must be a list with 24-168 points")
    for value in views:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value < 0
        ):
            raise ValueError("views must contain only non-negative numbers")
    return views


def _send(handler, status, payload):
    raw = json.dumps(payload, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.split("?")[0] != "/classify":
            return _send(self, 404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length).decode() or "null")
            result = classify(_extract_views(body))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            return _send(self, 422, {"error": "invalid series"})
        return _send(self, 200, result)

    def do_GET(self):
        return _send(self, 404, {"error": "not found"})

    do_PUT = do_GET
    do_DELETE = do_GET
    do_PATCH = do_GET

    def log_message(self, *args):
        pass


def run(port=8000):
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    run()
