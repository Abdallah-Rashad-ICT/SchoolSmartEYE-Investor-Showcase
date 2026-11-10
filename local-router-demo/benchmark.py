"""Measure real router round-trip latency using synthetic text only.

This is a client-side benchmark, not a hardware profiler. Run it from the
machine whose network path you want to measure. Results depend on the
router, workers, network, OS load, and request payload.
"""
import argparse
import json
import os
import platform
import statistics
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def percentile(values, fraction):
    ordered = sorted(values)
    if not ordered:
        return None
    index = max(0, min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction))))
    return round(ordered[index], 3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8100/route")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--text", default="SchoolSmartEYE synthetic router benchmark")
    args = parser.parse_args()

    if args.requests < 1 or args.requests > 10000:
        parser.error("--requests must be between 1 and 10000")
    if args.warmup < 0 or args.warmup > 1000:
        parser.error("--warmup must be between 0 and 1000")
    if len(args.text) > 8000:
        parser.error("--text must be at most 8000 characters")

    token = os.environ.get("SSE_DEMO_TOKEN", "local-demo-change-me")
    payload = json.dumps({"task": "text_stats", "text": args.text, "request_id": str(uuid.uuid4())}).encode()
    samples = []
    failures = []
    total = args.warmup + args.requests

    for number in range(total):
        request = Request(
            args.url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + token,
            },
            method="POST",
        )
        started = time.perf_counter()
        try:
            with urlopen(request, timeout=5) as response:
                body = json.loads(response.read())
                elapsed_ms = (time.perf_counter() - started) * 1000
                if response.status != 200 or body.get("status") != "completed":
                    raise RuntimeError("router returned an unexpected response")
                if number >= args.warmup:
                    samples.append(elapsed_ms)
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
            failures.append({"request": number + 1, "error": type(exc).__name__})

    elapsed_seconds = sum(samples) / 1000
    report = {
        "benchmark": "schoolsmarteye_local_router_round_trip",
        "measurement_scope": "client_observed_http_round_trip",
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "router_url": args.url,
        },
        "configuration": {
            "warmup_requests": args.warmup,
            "measured_requests": args.requests,
            "payload_characters": len(args.text),
            "task": "text_stats",
        },
        "results": {
            "successful_requests": len(samples),
            "failed_requests": len(failures),
            "latency_ms_min": round(min(samples), 3) if samples else None,
            "latency_ms_mean": round(statistics.mean(samples), 3) if samples else None,
            "latency_ms_p50": percentile(samples, 0.50),
            "latency_ms_p95": percentile(samples, 0.95),
            "latency_ms_max": round(max(samples), 3) if samples else None,
            "observed_requests_per_second": round(len(samples) / elapsed_seconds, 3) if elapsed_seconds else None,
        },
        "failures": failures[:20],
        "limitations": [
            "Client-observed round-trip latency, not isolated model inference time",
            "No CPU utilization, RAM utilization, GPU utilization, or energy measurement",
            "Results are environment-specific and are not a production performance claim",
        ],
    }
    print(json.dumps(report, indent=2))
    if not samples or failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
