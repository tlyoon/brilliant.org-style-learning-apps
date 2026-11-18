"""BSA210: source-free fixture mutation must never be masked by HTTP cache."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import tempfile
import unittest
from urllib.request import Request, urlopen

from scripts.check_course_preview_browser import QuietHandler


class BrowserFixtureCacheTests(unittest.TestCase):
    def setUp(self):
        context = tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        root = Path(context.name)
        self.file = root / "package.json"
        self.file.write_bytes(b'{"status":"original"}')
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(QuietHandler, directory=str(root)))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.thread.join, 5)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_port}/package.json"

    def test_test_server_never_returns_stale_bytes_after_source_tamper(self):
        with urlopen(self.url, timeout=10) as response:
            original_date = response.headers.get("Last-Modified")
            self.assertIn("no-store", response.headers["Cache-Control"])
            self.assertEqual(response.read(), b'{"status":"original"}')
        # Simulates the CI failure point: rewrite a previously fetched file
        # and request with the OLD conditional date within the same second.
        self.file.write_bytes(b'{"status":"corrupted"}')
        request = Request(self.url, headers={"If-Modified-Since": original_date})
        with urlopen(request, timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'{"status":"corrupted"}')
            self.assertIn("no-store", response.headers["Cache-Control"])

    def test_test_server_ignores_conditional_etag_on_replaced_fixture(self):
        self.file.write_bytes(b'{"status":"different"}')
        request = Request(self.url, headers={
            "If-None-Match": '"historical-fixture"',
            "If-Modified-Since": "Wed, 18 Nov 2099 12:00:00 GMT",
        })
        with urlopen(request, timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b'{"status":"different"}')
            self.assertEqual(response.headers["Pragma"], "no-cache")


if __name__ == "__main__":
    unittest.main()
