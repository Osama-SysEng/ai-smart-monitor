"""In-process operational metrics with bounded endpoint labels."""
from collections import Counter, defaultdict
from threading import Lock


class RuntimeMetrics:
    def __init__(self):
        self._lock = Lock()
        self._requests = Counter()
        self._errors = Counter()
        self._latency_totals = defaultdict(float)
        self._in_flight = 0

    def record(self, route: str, status_code: int, elapsed_seconds: float) -> None:
        key = route[:160]
        with self._lock:
            self._requests[key] += 1
            self._latency_totals[key] += elapsed_seconds
            if status_code >= 500:
                self._errors[key] += 1

    def started(self) -> None:
        with self._lock:
            self._in_flight += 1

    def completed(self) -> None:
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)

    def snapshot(self) -> dict:
        with self._lock:
            routes = {
                route: {
                    "requests": count,
                    "server_errors": self._errors[route],
                    "avg_latency_ms": round((self._latency_totals[route] / count) * 1000, 2),
                }
                for route, count in self._requests.items()
            }
            return {"in_flight": self._in_flight, "routes": routes}


runtime_metrics = RuntimeMetrics()
