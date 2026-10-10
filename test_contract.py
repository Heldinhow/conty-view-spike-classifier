"""HTTP contract tests. Literals below are the frozen README examples."""

import json
import threading
import unittest
import urllib.request
import urllib.error
from http.server import HTTPServer

from server import Handler

BASE_24 = [100, 102, 98, 101, 99, 103, 100, 97] * 3
BASE_168 = [100, 102, 98, 101, 99, 103, 100, 97] * 21
PLATEAU_24 = [100, 102, 98, 600, 600, 600, 55, 50] * 3

LEGIT_RESPONSE = {
    "verdict": "legitimate",
    "reason": (
        "base estável: pico de apenas 1.03x sobre a mediana "
        "(spike_ratio=1.03), sem queda abrupta (drop_ratio=0.961) "
        "nem repetição mecânica (flat_score=0.0)."
    ),
    "signals": {"spike_ratio": 1.03, "drop_ratio": 0.961, "flat_score": 0.0},
}
SUSPICIOUS_RESPONSE = {
    "verdict": "suspicious",
    "reason": (
        "pico comprado: pico de 5.941x sobre a mediana "
        "(spike_ratio=5.941) com platô mecânico "
        "(flat_score=0.4, drop_ratio=0.697)."
    ),
    "signals": {"spike_ratio": 5.941, "drop_ratio": 0.697, "flat_score": 0.4},
}


def _serve():
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, port


def _post(port, path, payload):
    return _request(port, "POST", path, payload)


def _request(port, method, path, payload):
    data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode())
    except urllib.error.HTTPError as err:
        raw = err.read()
        err.close()
        return err.code, json.loads(raw.decode()) if raw.strip() else None


class TestClassifyContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd, cls.port = _serve()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def test_legit_success_is_byte_equal_literal(self):
        status, body = _post(self.port, "/classify", {"views": BASE_24})
        self.assertEqual(status, 200)
        self.assertEqual(body, LEGIT_RESPONSE)

    def test_suspicious_success_is_byte_equal_literal(self):
        status, body = _post(self.port, "/classify", {"views": PLATEAU_24})
        self.assertEqual(status, 200)
        self.assertEqual(body, SUSPICIOUS_RESPONSE)

    def test_all_zero_series_is_inconclusive_200(self):
        status, body = _post(self.port, "/classify", {"views": [0] * 24})
        self.assertEqual(status, 200)
        self.assertEqual(body["verdict"], "inconclusive")
        self.assertEqual(
            body["signals"],
            {"spike_ratio": float("inf"), "drop_ratio": 1.0, "flat_score": 1.0},
        )

    def test_invalid_series_is_422(self):
        bad = [
            {"views": []},
            {"views": [100] * 23},
            {"views": [100] * 169},
            {"views": BASE_24[:23] + [-5]},
            {"views": BASE_24[:23] + ["x"]},
            {"views": BASE_24[:23] + [True]},
            {"views": BASE_24[:23] + [float("nan")]},
            {"views": BASE_24[:23] + [float("inf")]},
            {"views": BASE_24[:23] + [float("-inf")]},
            {},
            {"views": "nope"},
        ]
        for payload in bad:
            with self.subTest(payload=str(payload)[:60]):
                status, _ = _post(self.port, "/classify", payload)
                self.assertEqual(status, 422)

    def test_window_edges_24_and_168_are_accepted(self):
        for views in (BASE_24, BASE_168):
            with self.subTest(n=len(views)):
                status, body = _post(self.port, "/classify", {"views": views})
                self.assertEqual(status, 200)
                self.assertEqual(body, LEGIT_RESPONSE)

    def test_unknown_route_is_404_with_precedence_over_422(self):
        status, _ = _post(self.port, "/nope", {"views": []})
        self.assertEqual(status, 404)
        status, _ = _post(self.port, "/nope", {"views": BASE_24})
        self.assertEqual(status, 404)

    def test_unknown_route_is_404_for_all_methods(self):
        for method in ("GET", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
            with self.subTest(method=method):
                status, body = _request(self.port, method, "/nope", b"{}")
                self.assertEqual(status, 404)
                if method != "HEAD":
                    self.assertEqual(body, {"error": "not found"})


if __name__ == "__main__":
    unittest.main()
