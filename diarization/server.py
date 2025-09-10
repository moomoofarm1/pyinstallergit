"""Minimal placeholder diarization backend server."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    """Serve a simple health check endpoint."""

    def do_GET(self):  # noqa: N802 - required method name
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()


def run() -> None:
    host = os.environ.get("ALF_SERVER_HOST", "127.0.0.1")
    port = int(os.environ.get("ALF_SERVER_PORT", "9090"))
    print("hello word")
    server = HTTPServer((host, port), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    run()

