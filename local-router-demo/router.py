"""Local demo router with enrollment, SQLite replay protection and failover."""
import ipaddress
import itertools
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from state_store import SQLiteStateStore

TOKEN = os.environ.get("SSE_DEMO_TOKEN", "local-demo-change-me")
HOST = os.environ.get("SSE_BIND", "127.0.0.1")
PORT = int(os.environ.get("SSE_ROUTER_PORT", "8100"))
RAW = os.environ.get("SSE_NODES", "PC2=http://127.0.0.1:8101,PC3=http://127.0.0.1:8102")
STATIC_NODES = [tuple(item.split("=", 1)) for item in RAW.split(",") if "=" in item]
STORE = SQLiteStateStore()
cycle = itertools.cycle(STATIC_NODES or [("no-node", "http://127.0.0.1:1")])
MAX_BODY = 16_384


def post_json(url, path, body, timeout=2):
    data = json.dumps(body).encode()
    req = Request(url + path, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer " + TOKEN,
    })
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


def registered_nodes():
    combined = {name: url for name, url in STATIC_NODES}
    for item in STORE.list_nodes():
        combined[item["node_id"]] = item["url"]
    return list(combined.items())


def safe_enrollment_url(value):
    """Only accept plain HTTP endpoints on loopback/private IPs or .local hosts."""
    if not isinstance(value, str) or len(value) > 255:
        return False
    try:
        parsed = urlsplit(value)
        if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password:
            return False
        if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
            return False
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".local"):
            return True
        address = ipaddress.ip_address(host)
        return address.is_private or address.is_loopback
    except ValueError:
        return False


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        return self.headers.get("Authorization") == "Bearer " + TOKEN

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > MAX_BODY:
            raise ValueError("invalid_body_size")
        body = json.loads(self.rfile.read(length))
        if not isinstance(body, dict):
            raise ValueError("invalid_json_object")
        return body

    def do_GET(self):
        if self.path == "/health":
            states = []
            for name, url in registered_nodes():
                try:
                    with urlopen(url + "/health", timeout=1) as response:
                        states.append({"node": name, "healthy": response.status == 200})
                except Exception:
                    states.append({"node": name, "healthy": False})
            return self.send_json(200, {
                "router": "ok", "nodes": states,
                "mode": "round_robin_with_failover",
                "replay_guard": "sqlite_persistent",
            })
        if self.path == "/nodes":
            if not self.authorized():
                return self.send_json(401, {"error": "unauthorized"})
            return self.send_json(200, {"nodes": [
                {"node_id": name, "url": url} for name, url in registered_nodes()
            ]})
        return self.send_json(404, {"error": "not_found"})

    def do_POST(self):
        if self.path not in ("/route", "/register"):
            return self.send_json(404, {"error": "not_found"})
        if not self.authorized():
            return self.send_json(401, {"error": "unauthorized"})
        try:
            body = self.read_body()
        except Exception:
            return self.send_json(400, {"error": "invalid_json_or_body_size"})

        if self.path == "/register":
            node_id, url = body.get("node_id"), body.get("url")
            capabilities = body.get("capabilities", ["echo", "text_stats"])
            if (not isinstance(node_id, str) or not 1 <= len(node_id) <= 64
                    or not all(c.isalnum() or c in "-_" for c in node_id)
                    or not safe_enrollment_url(url)
                    or not isinstance(capabilities, list)
                    or not all(c in ("echo", "text_stats") for c in capabilities)):
                return self.send_json(400, {"error": "invalid_node_registration"})
            STORE.register_node(node_id, url.rstrip("/"), capabilities)
            return self.send_json(201, {"status": "registered", "node_id": node_id})
        
        request_id = body.get("request_id")
        if not isinstance(request_id, str) or not 8 <= len(request_id) <= 128:
            return self.send_json(400, {"error": "request_id_required"})
        if not STORE.claim_request(request_id):
            return self.send_json(409, {"error": "replay_detected"})
        if body.get("task") not in ("echo", "text_stats") or not isinstance(body.get("text", ""), str):
            return self.send_json(400, {"error": "unsupported_task_or_text"})
        if len(body.get("text", "")) > 8000:
            return self.send_json(400, {"error": "text_too_long"})

        nodes = registered_nodes()
        if not nodes:
            return self.send_json(503, {"status": "unavailable", "message": "No workers registered"})
        start = next(cycle) if STATIC_NODES else nodes[0]
        ordered = [start] + [item for item in nodes if item != start]
        attempts = []
        for name, url in ordered:
            started = perf_counter()
            try:
                result = post_json(url, "/execute", body)
                return self.send_json(200, {
                    "status": "completed", "selected_node": name,
                    "router_ms": round((perf_counter() - started) * 1000, 3),
                    "attempts": attempts, "worker_result": result,
                })
            except Exception as exc:
                attempts.append({"node": name, "error": type(exc).__name__})
        return self.send_json(503, {
            "status": "unavailable", "attempts": attempts,
            "message": "No configured worker accepted the demo task",
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    if not STATIC_NODES and not STORE.list_nodes():
        raise SystemExit("Configure SSE_NODES or register at least one worker")
    print(f"Demo router listening on {HOST}:{PORT}; workers={len(registered_nodes())}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
