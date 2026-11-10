"""Safe demo worker with basic, best-effort host resource telemetry."""
import json
import os
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import perf_counter

TOKEN = os.environ.get("SSE_DEMO_TOKEN", "local-demo-change-me")
HOST = os.environ.get("SSE_BIND", "127.0.0.1")
PORT = int(os.environ.get("SSE_PORT", "8101"))
MAX_BODY = 16_384


def resource_metrics():
    cpu_count = os.cpu_count() or 1
    load_1m = None
    load_per_cpu = None
    try:
        load_1m = os.getloadavg()[0]
        load_per_cpu = load_1m / cpu_count
    except (AttributeError, OSError):
        pass

    memory_total = None
    memory_available = None
    try:
        if os.name == "posix":
            page_size = os.sysconf("SC_PAGE_SIZE")
            memory_total = os.sysconf("SC_PHYS_PAGES") * page_size
            memory_available = os.sysconf("SC_AVPHYS_PAGES") * page_size
    except (ValueError, OSError, AttributeError):
        pass

    if memory_total is None or memory_available is None:
        try:
            with open("/proc/meminfo", encoding="ascii") as source:
                values = {}
                for line in source:
                    key, value = line.split(":", 1)
                    if key in ("MemTotal", "MemAvailable"):
                        values[key] = int(value.strip().split()[0]) * 1024
                memory_total = values.get("MemTotal")
                memory_available = values.get("MemAvailable")
        except (OSError, ValueError, KeyError):
            pass

    return {
        "logical_cpu_count": cpu_count,
        "load_1m": round(load_1m, 4) if load_1m is not None else None,
        "load_per_cpu": round(load_per_cpu, 4) if load_per_cpu is not None else None,
        "memory_total_bytes": memory_total,
        "memory_available_bytes": memory_available,
        "telemetry_source": "host_os_best_effort",
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != "/health":
            return self.send_json(404, {"error": "not_found"})
        self.send_json(200, {
            "status": "ok",
            "node": os.environ.get("SSE_NODE_ID", "PC2"),
            "capabilities": ["echo", "text_stats"],
            "metrics": resource_metrics(),
        })

    def do_POST(self):
        if self.path != "/execute":
            return self.send_json(404, {"error": "not_found"})
        if self.headers.get("Authorization") != "Bearer " + TOKEN:
            return self.send_json(401, {"error": "unauthorized"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n < 1 or n > MAX_BODY:
                return self.send_json(413, {"error": "invalid_body_size"})
            payload = json.loads(self.rfile.read(n))
        except Exception:
            return self.send_json(400, {"error": "invalid_json"})
        if not isinstance(payload, dict):
            return self.send_json(400, {"error": "invalid_json_object"})
        task = payload.get("task")
        text = payload.get("text", "")
        if not isinstance(text, str) or len(text) > 8000:
            return self.send_json(400, {"error": "text_must_be_string_under_8000_chars"})
        started = perf_counter()
        if task == "echo":
            result = {"echo": text}
        elif task == "text_stats":
            result = {
                "characters": len(text),
                "words": len(text.split()),
                "lines": len(text.splitlines()) or (1 if text else 0),
            }
        else:
            return self.send_json(400, {
                "error": "task_not_allowlisted",
                "allowed": ["echo", "text_stats"],
            })
        self.send_json(200, {
            "node": os.environ.get("SSE_NODE_ID", "PC2"),
            "task": task,
            "result": result,
            "execution_ms": round((perf_counter() - started) * 1000, 3),
            "synthetic_data_only": True,
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"Demo worker {os.environ.get('SSE_NODE_ID', 'PC2')} listening on {HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
