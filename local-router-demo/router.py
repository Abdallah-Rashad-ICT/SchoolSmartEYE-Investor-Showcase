"""Local demo router with enrollment, durable replay guard and resource ranking."""
import ipaddress
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import perf_counter
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from scheduler import rank_workers
from state_store import SQLiteStateStore

TOKEN = os.environ.get("SSE_DEMO_TOKEN", "local-demo-change-me")
HOST = os.environ.get("SSE_BIND", "127.0.0.1")
PORT = int(os.environ.get("SSE_ROUTER_PORT", "8100"))
RAW = os.environ.get("SSE_NODES", "PC2=http://127.0.0.1:8101,PC3=http://127.0.0.1:8102")
STATIC_NODES = [tuple(item.split("=", 1)) for item in RAW.split(",") if "=" in item]
STORE = SQLiteStateStore()
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
    combined = {
        name: {"node_id": name, "url": url, "capabilities": ["echo", "text_stats"]}
        for name, url in STATIC_NODES
    }
    for item in STORE.list_nodes():
        combined[item["node_id"]] = {
            "node_id": item["node_id"],
            "url": item["url"],
            "capabilities": item["capabilities"],
        }
    return list(combined.values())


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


def probe_workers():
    results = []
    for node in registered_nodes():
        item = dict(node)
        try:
            with urlopen(item["url"] + "/health", timeout=1) as response:
                health = json.loads(response.read())
            item["healthy"] = response.status == 200 and health.get("status") == "ok"
            item["metrics"] = health.get("metrics", {})
            item["reported_node"] = health.get("node")
            if isinstance(health.get("capabilities"), list):
                item["capabilities"] = [
                    capability for capability in item["capabilities"]
                    if capability in health["capabilities"]
                ]
        except Exception as exc:
            item["healthy"] = False
            item["metrics"] = {}
            item["probe_error"] = type(exc).__name__
        results.append(item)
    return results


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
            for node in probe_workers():
                states.append({
                    "node": node["node_id"],
                    "healthy": node["healthy"],
                    "metrics": node.get("metrics", {}),
                })
            return self.send_json(200, {
                "router": "ok",
                "nodes": states,
                "scheduler": "cpu_memory_best_effort",
                "replay_guard": "sqlite_persistent",
            })
        if self.path == "/nodes":
            if not self.authorized():
                return self.send_json(401, {"error": "unauthorized"})
            return self.send_json(200, {"nodes": [
                {"node_id": n["node_id"], "url": n["url"],
                 "capabilities": n["capabilities"]}
                for n in registered_nodes()
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
                    or not capabilities
                    or not all(c in ("echo", "text_stats") for c in capabilities)):
                return self.send_json(400, {"error": "invalid_node_registration"})
            STORE.register_node(node_id, url.rstrip("/"), capabilities)
            return self.send_json(201, {"status": "registered", "node_id": node_id})

        request_id = body.get("request_id")
        task, text_value = body.get("task"), body.get("text", "")
        if not isinstance(request_id, str) or not 8 <= len(request_id) <= 128:
            return self.send_json(400, {"error": "request_id_required"})
        if task not in ("echo", "text_stats") or not isinstance(text_value, str):
            return self.send_json(400, {"error": "unsupported_task_or_text"})
        if len(text_value) > 8000:
            return self.send_json(400, {"error": "text_too_long"})
        if not STORE.claim_request(request_id):
            return self.send_json(409, {"error": "replay_detected"})

        ranked = rank_workers(probe_workers(), task)
        if not ranked:
            return self.send_json(503, {
                "status": "unavailable",
                "message": "No healthy worker supports this task",
            })

        attempts = []
        for node in ranked:
            started = perf_counter()
            try:
                result = post_json(node["url"], "/execute", body)
                return self.send_json(200, {
                    "status": "completed",
                    "selected_node": node["node_id"],
                    "scheduler": "cpu_memory_best_effort",
                    "resource_score": node["resource_score"],
                    "worker_metrics": node.get("metrics", {}),
                    "router_ms": round((perf_counter() - started) * 1000, 3),
                    "attempts": attempts,
                    "worker_result": result,
                })
            except Exception as exc:
                attempts.append({"node": node["node_id"], "error": type(exc).__name__})
        return self.send_json(503, {
            "status": "unavailable",
            "attempts": attempts,
            "message": "No configured worker accepted the demo task",
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    if not STATIC_NODES and not STORE.list_nodes():
        raise SystemExit("Configure SSE_NODES or register at least one worker")
    print(f"Demo router listening on {HOST}:{PORT}; workers={len(registered_nodes())}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
