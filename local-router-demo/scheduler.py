"""Transparent, conservative resource scoring for demo workers."""


def resource_score(metrics):
    """Lower is better. Missing telemetry is treated as neutral, not zero."""
    if not isinstance(metrics, dict):
        metrics = {}
    cpu = metrics.get("load_per_cpu")
    if not isinstance(cpu, (int, float)) or cpu < 0:
        cpu_pressure = 0.75
    else:
        cpu_pressure = min(float(cpu), 2.0) / 2.0

    available = metrics.get("memory_available_bytes")
    total = metrics.get("memory_total_bytes")
    if (isinstance(available, int) and isinstance(total, int)
            and total > 0 and 0 <= available <= total):
        memory_pressure = 1.0 - (available / total)
    else:
        memory_pressure = 0.5

    return round((0.7 * cpu_pressure) + (0.3 * memory_pressure), 6)


def rank_workers(workers, task):
    """Return healthy, capable worker dicts ordered by resource score."""
    eligible = []
    for worker in workers:
        if not worker.get("healthy"):
            continue
        if task not in worker.get("capabilities", []):
            continue
        item = dict(worker)
        item["resource_score"] = resource_score(item.get("metrics"))
        eligible.append(item)
    return sorted(eligible, key=lambda item: (item["resource_score"], item["node_id"]))
