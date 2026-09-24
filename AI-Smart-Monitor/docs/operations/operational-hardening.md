# Operational Hardening Runbook

AI-Smart-Monitor now separates **service accounts** from short-lived, revocable bearer sessions. Service account secrets are persisted only as scrypt hashes, and each account is tied to a tenant and an explicit role set. The raw key is returned only during provisioning; it must be injected into an approved secret manager rather than copied into source control.

| Operational control | Implementation | Required production action |
|---|---|---|
| API identity | Hashed service account key; optional revocable session | Set `AUTH_MODE=service_accounts`, `REQUIRE_API_KEY=true`, and an explicit `SESSION_SECRET`. |
| Authorization | Tenant-aware capabilities at import, case, anomaly, ERP, audit, and operations surfaces | Issue least-privilege `operator`, `integration`, `auditor`, or `viewer` roles; avoid `admin` for automation. |
| ERP delivery | Outbox, idempotency keys, retry schedule, delivery attempts, and circuit breaker | Run a dedicated worker in staging; do not enable ERP writes without a real approval process. |
| Database | PostgreSQL migration `0002_operational_hardening.sql` | Apply once from a controlled job, back up first, then verify indexes and tenant defaults. |
| Readiness | `/api/v1/ready` returns 503 if database connectivity fails | Configure the orchestrator to use readiness, not liveness, for traffic admission. |
| Load checks | Bounded `tools/load_probe.py` | Use only local or approved staging target and a dedicated short-lived token. |

The service calls `Base.metadata.create_all` only for development/test convenience. A production deployment should apply the SQL migration from an immutable release artifact, run API replicas with a restricted application database role, and execute delivery work in a separate process with a narrowly scoped ERP credential.

> The load probe is a measurement harness, not a capacity claim. Increase concurrency incrementally in staging, inspect p95/p99 latency, queue depth, connection pool pressure, error rates, and circuit-breaker events before making any throughput decision.
