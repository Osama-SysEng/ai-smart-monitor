"""Bounded, authorization-aware load probe for local or approved staging targets."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import statistics
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx


def assert_safe_target(url: str, allow_remote: bool) -> None:
    hostname = urlparse(url).hostname
    if hostname not in {"localhost", "127.0.0.1", "::1"} and not allow_remote:
        raise ValueError("Remote targets require --allow-remote and an approved staging window")


def one_request(base_url: str, path: str, token: str | None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    started = time.perf_counter()
    try:
        response = httpx.get(base_url.rstrip("/") + path, headers=headers, timeout=10)
        return {"status": response.status_code, "latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except httpx.HTTPError as exc:
        return {"status": 0, "latency_ms": round((time.perf_counter() - started) * 1000, 2), "error": type(exc).__name__}


def summarize(results: list[dict]) -> dict:
    latency = sorted(item["latency_ms"] for item in results)
    percentile = lambda fraction: latency[max(0, min(len(latency) - 1, int(len(latency) * fraction + 0.999) - 1))] if latency else None
    success = sum(200 <= item["status"] < 400 for item in results)
    return {"requests": len(results), "success_rate": round(success / len(results), 4) if results else 0, "p50_ms": percentile(0.5), "p95_ms": percentile(0.95), "p99_ms": percentile(0.99), "max_ms": max(latency, default=None)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--path", default="/api/v1/health/ready")
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--allow-remote", action="store_true")
    parser.add_argument("--output", default="reports/load/latest.json")
    args = parser.parse_args()
    if args.requests < 1 or args.concurrency < 1:
        parser.error("requests and concurrency must be positive")
    assert_safe_target(args.base_url, args.allow_remote)
    token = os.getenv("LOADTEST_BEARER_TOKEN")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        results = list(executor.map(lambda _: one_request(args.base_url, args.path, token), range(args.requests)))
    report = {"target": args.base_url, "path": args.path, "configuration": {"requests": args.requests, "concurrency": args.concurrency}, "summary": summarize(results)}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
