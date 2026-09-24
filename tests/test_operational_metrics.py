from app.core.metrics import RuntimeMetrics
from tools.load_probe import assert_safe_target, summarize


def test_metrics_aggregate_by_route():
    metrics = RuntimeMetrics()
    metrics.started()
    metrics.record("/api/v1/imports", 201, 0.02)
    metrics.record("/api/v1/imports", 500, 0.04)
    metrics.completed()
    snapshot = metrics.snapshot()
    assert snapshot["in_flight"] == 0
    assert snapshot["routes"]["/api/v1/imports"]["requests"] == 2
    assert snapshot["routes"]["/api/v1/imports"]["server_errors"] == 1


def test_load_probe_requires_explicit_remote_opt_in():
    try:
        assert_safe_target("https://staging.example.test", allow_remote=False)
        assert False, "remote target should require opt-in"
    except ValueError:
        pass
    assert summarize([{"status": 200, "latency_ms": 10.0}, {"status": 503, "latency_ms": 30.0}])["success_rate"] == 0.5
