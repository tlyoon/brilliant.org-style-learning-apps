#!/usr/bin/env python3
"""Serve the repository locally for the dependency-free learner prototype."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=ROOT, **kwargs))
    print("Open http://127.0.0.1:8000/app/ (Ctrl+C to stop)")
    server.serve_forever()


if __name__ == "__main__":
    main()
