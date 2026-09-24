METRIC_PREFIX = "smart_monitor.anomalies"

def metric(name: str) -> str:
    return f"{METRIC_PREFIX}.{name}"

def tags(status: str, correlation_id: str | None) -> dict[str, str]:
    return {"status": status, "correlation_id": correlation_id or "unassigned"}
