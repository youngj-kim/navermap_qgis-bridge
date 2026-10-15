import json
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Full, Queue

from .settings import naver_javascript_key
from .viewer_document import build_viewer_html, external_bridge_script


EXTERNAL_BRIDGE_SCRIPT = external_bridge_script()
COMMANDS = {"move-center", "zoom-view", "roadview-state", "request-route", "cancel-route",
            "route-point", "clear-route-point", "clear-route-points",
            "request-local-search", "select-route-guidance", "select-route-history",
            "load-route-history", "delete-route-history", "export-route-history",
            "refresh-route-history"}


class ExclusiveHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class NaverExternalBridgeServer:
    def __init__(self, host="127.0.0.1", port=8083):
        if host != "127.0.0.1":
            raise ValueError("External bridge must bind to loopback")
        self.host = host
        self.port = port
        self._token = secrets.token_urlsafe(32)
        self._server = None
        self._thread = None
        self._events = Queue(maxsize=512)
        self._lock = threading.RLock()
        self._epoch = 0
        self._accepting = True
        self._outbound_events = []
        self._outbound_sequence = 0
        self._center = None
        self._center_sequence = 0

    @property
    def url(self):
        if self._server is None:
            return ""
        _host, port = self._server.server_address
        return f"http://localhost:{port}/#token={self._token}"

    def start(self):
        if self._server is not None:
            return self.url

        handler = self._make_handler()
        self._token = secrets.token_urlsafe(32)
        self._server = ExclusiveHTTPServer((self.host, self.port), handler)
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

    def next_event(self):
        try:
            return self._events.get_nowait()
        except Empty:
            return None

    def drain_events(self):
        events = []
        while True:
            try:
                events.append(self._events.get_nowait())
            except Empty:
                return events

    def set_view(self, lon, lat, meters_per_pixel, preserve_roadview=False):
        with self._lock:
            self.set_center(lon, lat)
            self._center.update(meters_per_pixel=float(meters_per_pixel),
                                preserve_roadview=bool(preserve_roadview))

    def reset_project(self, epoch, accepting=True):
        with self._lock:
            self._epoch = epoch
            self._accepting = accepting
            self._center = None
            self._outbound_events = []
            self.drain_events()

    def enqueue(self, event_type, payload):
        with self._lock:
            if not self._accepting or payload.get("_epoch") != self._epoch:
                return 409
            try:
                self._events.put_nowait({"type": event_type, "payload": payload, "epoch": self._epoch})
            except Full:
                return 429
            return 200

    def emit_signal(self, name, *args):
        with self._lock:
            self._outbound_sequence += 1
            self._outbound_events.append({"sequence": self._outbound_sequence,
                                          "epoch": self._epoch, "signal": name,
                                          "args": list(args)})
            self._outbound_events = self._outbound_events[-100:]

    def _viewer_html(self):
        return build_viewer_html(naver_javascript_key(), EXTERNAL_BRIDGE_SCRIPT)

    def _make_handler(self):
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def _authorized(self, api=False):
                port = bridge._server.server_address[1]
                hosts = {f"localhost:{port}", f"127.0.0.1:{port}"}
                if self.headers.get("Host", "").lower() not in hosts:
                    self.send_error(403)
                    return False
                origin = self.headers.get("Origin")
                if origin is not None and origin not in {"http://" + host for host in hosts}:
                    self.send_error(403)
                    return False
                if api and not secrets.compare_digest(self.headers.get("X-Bridge-Token", "").encode("utf-8"), bridge._token.encode("ascii")):
                    self.send_error(403)
                    return False
                return True

            def do_GET(self):
                if not self._authorized(api=self.path.startswith("/api/")):
                    return
                if self.path in ("/", "/viewer"):
                    self._send_text(bridge._viewer_html(), "text/html")
                    return
                if self.path == "/api/state":
                    with bridge._lock:
                        state = {"center": bridge._center, "epoch": bridge._epoch,
                                 "accepting": bridge._accepting,
                                 "sequence": bridge._outbound_sequence}
                    self._send_json(state)
                    return
                if self.path.startswith("/api/events"):
                    since = 0
                    if "?since=" in self.path:
                        try:
                            since = int(self.path.rsplit("?since=", 1)[-1])
                        except ValueError:
                            since = 0
                    with bridge._lock:
                        events = [
                                event
                                for event in bridge._outbound_events
                                if event["sequence"] > since
                            ]
                        epoch = bridge._epoch
                        gap = bool(bridge._outbound_events and since < bridge._outbound_events[0]["sequence"] - 1)
                    self._send_json({"events": events, "epoch": epoch, "gap": gap})
                    return

                self.send_error(404)

            def do_POST(self):
                if not self._authorized(api=True):
                    return
                if self.path not in {"/api/" + command for command in COMMANDS}:
                    self.send_error(404)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0") or "0")
                except ValueError:
                    self.send_error(400)
                    return
                if not 0 <= length <= 65536:
                    self.send_error(413)
                    return
                raw = self.rfile.read(length) if length else b"{}"
                if self.headers.get_content_type() != "application/json":
                    self.send_error(415)
                    return
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self.send_error(400)
                    return
                if not isinstance(payload, dict):
                    self.send_error(400)
                    return

                event_type = self.path.rsplit("/", 1)[-1].replace("-", "_")
                status = bridge.enqueue(event_type, payload)
                if status != 200:
                    self.send_error(status)
                    return
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
                self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def _send_json(self, payload):
                self._send_text(
                    json.dumps(payload, ensure_ascii=False),
                    "application/json",
                )

        return Handler

