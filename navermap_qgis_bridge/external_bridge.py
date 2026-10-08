import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Queue

from .settings import naver_javascript_key
from .viewer_document import build_viewer_html, external_bridge_script


EXTERNAL_BRIDGE_SCRIPT = external_bridge_script()


class NaverExternalBridgeServer:
    def __init__(self, host="127.0.0.1", port=8082):
        self.host = host
        self.port = port
        self._server = None
        self._thread = None
        self._events = Queue()
        self._outbound_events = []
        self._outbound_sequence = 0
        self._center = None
        self._center_sequence = 0

    @property
    def url(self):
        if self._server is None:
            return ""
        _host, port = self._server.server_address
        return f"http://localhost:{port}/"

    def start(self):
        if self._server is not None:
            return self.url

        handler = self._make_handler()
        self._server = ThreadingHTTPServer((self.host, self.port), handler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="NaverQgisExternalBridge",
            daemon=True,
        )
        self._thread.start()
        return self.url

    def stop(self):
        if self._server is None:
            return

        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None

    def set_center(self, lon, lat):
        self._center_sequence += 1
        self._center = {
            "lon": float(lon),
            "lat": float(lat),
            "sequence": self._center_sequence,
        }

    def drain_events(self):
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                return events

    def emit_signal(self, name, *args):
        self._outbound_sequence += 1
        self._outbound_events.append(
            {
                "sequence": self._outbound_sequence,
                "signal": name,
                "args": list(args),
            }
        )
        if len(self._outbound_events) > 100:
            self._outbound_events = self._outbound_events[-100:]

    def _viewer_html(self):
        return build_viewer_html(naver_javascript_key(), EXTERNAL_BRIDGE_SCRIPT)

    def _make_handler(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path in ("/", "/viewer"):
                    self._send_text(bridge._viewer_html(), "text/html")
                    return
                if self.path == "/api/state":
                    self._send_json({"center": bridge._center})
                    return
                if self.path.startswith("/api/events"):
                    since = 0
                    if "?since=" in self.path:
                        try:
                            since = int(self.path.rsplit("?since=", 1)[-1])
                        except ValueError:
                            since = 0
                    self._send_json(
                        {
                            "events": [
                                event
                                for event in bridge._outbound_events
                                if event["sequence"] > since
                            ]
                        }
                    )
                    return

                self.send_error(404)

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except json.JSONDecodeError:
                    payload = {}

                event_type = self.path.rsplit("/", 1)[-1].replace("-", "_")
                bridge._events.put({"type": event_type, "payload": payload})
                self._send_json({"ok": True})

            def log_message(self, _format, *_args):
                return

            def _send_text(self, body, content_type):
                encoded = body.encode("utf-8")
                self.send_response(200)
                self.send_header(
                    "Content-Type",
                    f"{content_type}; charset=utf-8",
                )
                self.send_header("Cache-Control", "no-store, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _send_json(self, payload):
                self._send_text(
                    json.dumps(payload, ensure_ascii=False),
                    "application/json",
                )

        return Handler

