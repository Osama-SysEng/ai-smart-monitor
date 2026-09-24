# Production Readiness Guide

## Scope and trust boundary

The Smart Monitor is designed so that reconciliation and financial-impact calculations remain deterministic. AI may add an interpretation to retained evidence, but it is not a decision authority and cannot mutate source data, close a case, or write to ERP. Every sensitive mutation must have an authenticated actor, a request correlation identifier, and an audit event.

> The project source is ready for controlled staging validation. It is not a claim that any third-party ERP, messaging, or AI provider is connected or production-approved.

## Required environment contract

| Variable | Production requirement | Why it matters |
|---|---|---|
| `ENVIRONMENT` | `production` | Enables production configuration validation. |
| `DATABASE_URL` | Managed PostgreSQL URL | SQLite is rejected in production. |
| `CORS_ORIGINS` | Explicit HTTPS dashboard origins | Prevents wildcard cross-origin access. |
| `REQUIRE_API_KEY` | `true` | Requires API-key protection for non-health API calls. |
| `API_KEY` | 24+ character secret in a secret manager | Protects the operational API boundary. |
| `MAX_UPLOAD_BYTES` | Explicit limit | Constrains upload pressure and parser risk. |
| `MAX_IMPORT_ROWS` | Explicit limit matched to worker capacity | Prevents one import from exhausting the service. |

Keep these values in deployment-secret storage. Never place real keys in `.env.example`, source control, browser bundles, or uploaded data files.

## Staging acceptance sequence

First provision a non-production PostgreSQL database, Redis, and a dashboard origin. Then configure the environment contract, run `pytest -q`, and run `pnpm build` inside `frontend/`. Start with two approved source datasets and a single reconciliation rule. Review every quarantined row, every newly opened anomaly, and the generated audit chain before enabling any external notification.

The ERP connector must remain in outbox-only mode until a named approver is available. Events whose type is `ERP_WRITE`, `SOURCE_MUTATION`, or `FINANCIAL_ADJUSTMENT` require an `approval_reference`; duplicate events are suppressed by a deterministic idempotency key.

## Scaling path

The current source provides a strong application contract, not a capacity promise. For growth, move reconciliation execution to workers backed by Redis, partition source facts by tenant and business date, use PostgreSQL indexes and pagination for read models, place the API behind a managed load balancer, and use object storage rather than process memory for large files. WebSocket or webhook workers must share state through Redis or a queue; do not depend on in-memory state across replicas.

## Incident response

If an import fails, retain its metadata and bounded error report, correct the source file, and submit a new file hash. If reconciliation produces a critical anomaly, open one investigation case, record the decision and reason, and do not issue ERP writes without an approval reference. If a secret may have leaked, revoke it at the provider, rotate the deployment secret, and inspect audit records by correlation identifier.
