from __future__ import annotations

import http.server
import socketserver
import urllib.error
import urllib.request


TARGET_BASE = "http://127.0.0.1:5600"
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 5601


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_PUT(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()

    def do_OPTIONS(self) -> None:
        self._proxy()

    def _proxy(self) -> None:
        target_url = f"{TARGET_BASE}{self.path}"
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length > 0 else None
        request = urllib.request.Request(
            target_url,
            data=body,
            method=self.command,
            headers=self._forward_headers(),
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() in {"transfer-encoding", "connection", "content-encoding"}:
                        continue
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() in {"transfer-encoding", "connection", "content-encoding"}:
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except Exception as exc:
            payload = str(exc).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def _forward_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        for key, value in self.headers.items():
            if key.lower() in {"host", "content-length", "connection"}:
                continue
            headers[key] = value
        return headers

    def log_message(self, format: str, *args: object) -> None:
        return


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    with ThreadingTCPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler) as server:
        server.serve_forever()
