# Local Router Live Demo (safe proof of concept)

This is a **real local HTTP routing proof of concept**, not a production deployment. Start two worker processes (or run one worker on each test PC), then start the router. The router performs real HTTP health checks, round-robin node selection and failover; the worker executes only two allowlisted synthetic text tasks.

## Requirements
- Python 3.10+
- Standard library only; no third-party packages.

## Run locally (two terminals for workers, one for router)

Set the same demo token in every terminal. Replace the example token with a fresh random value.

**Terminal 1 — worker PC2**
```bash
# Linux/macOS
export SSE_DEMO_TOKEN="replace-with-a-long-random-demo-token"
export SSE_NODE_ID="PC2"
export SSE_PORT="8101"
python worker.py
```

**Terminal 2 — worker PC3**
```bash
export SSE_DEMO_TOKEN="replace-with-a-long-random-demo-token"
export SSE_NODE_ID="PC3"
export SSE_PORT="8102"
python worker.py
```

**Terminal 3 — router**
```bash
export SSE_DEMO_TOKEN="replace-with-a-long-random-demo-token"
export SSE_NODES="PC2=http://127.0.0.1:8101,PC3=http://127.0.0.1:8102"
python router.py
```

For separate computers on a trusted LAN, set each worker's `SSE_BIND=0.0.0.0`, use its LAN IP in `SSE_NODES`, and restrict firewall access to the school LAN. The router's default bind is loopback; expose it only behind an authenticated TLS reverse proxy after security review. **This demo uses plain HTTP and a shared demo bearer token; do not expose it to the public internet or use real student data.**

## Try it

Health:
```bash
curl http://127.0.0.1:8100/health
```

Route a synthetic task:
```bash
curl -X POST http://127.0.0.1:8100/route \
  -H "Authorization: Bearer replace-with-a-long-random-demo-token" \
  -H "Content-Type: application/json" \
  -d '{"task":"text_stats","text":"SchoolSmartEYE local AI demo"}'
```

Allowed tasks: `echo`, `text_stats`. No arbitrary shell, Python, model execution, camera access, or student data processing is provided.

## Test
```bash
python -m unittest -v
```

## What this proves — and does not prove
- Proves local HTTP request/response between a router and worker, health checks, simple round-robin selection, failover attempts, and bearer-token gating.
- Does **not** prove PC1–PC5 production security, mTLS, durable replay protection, hardware-aware scheduling, GPU/CPU benchmarking, offline resilience, high availability, or a validated school deployment.


## Measure observed router latency

After starting the router and workers, run this from the client machine:

```bash
# Set the same token used by the router and workers
export SSE_DEMO_TOKEN="replace-with-a-long-random-demo-token"
python benchmark.py --url http://127.0.0.1:8100/route --warmup 5 --requests 50
```

On Windows PowerShell:

```powershell
$env:SSE_DEMO_TOKEN = "replace-with-a-long-random-demo-token"
python benchmark.py --url http://127.0.0.1:8100/route --warmup 5 --requests 50
```

The JSON report includes OS/Python/CPU-count metadata, successful and failed requests, observed round-trip min/mean/p50/p95/max latency, and observed requests per second. Save reports from each test PC and compare them under the same workload and network conditions. This script does not measure CPU/RAM utilization, GPU utilization, power, or model inference; do not present its results as those measurements or as a production guarantee. A run with any failed request exits non-zero.
