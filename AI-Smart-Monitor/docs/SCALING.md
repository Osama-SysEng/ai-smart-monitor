# SCALING — AI-Smart-Monitor

## Bottlenecks (current)
1. **DB connection pool** — `app/db/session.py` uses SQLAlchemy `QueuePool`
   (`pool_size` + `max_overflow`). Bursts beyond `pool_size + max_overflow`
   block up to `pool_timeout` then fail. SQLite dev mode has no pooling
   (single-file, `check_same_thread=False`) — not production-safe.
2. **Unbounded list responses** — fixed: every list endpoint now takes
   `limit` (default 50, max 500) + `offset` (see table below).
3. **Per-request identity check** — `app/main.py:request_controls` opens a DB
   session per non-public request; keep queries indexed on `tenant_id`.
4. **Rate limiter is in-memory per process** (`_hits` in `app/main.py`) —
   does not share state across workers/replicas.

## Tuning variables (.env)
| Variable | Default | Effect |
|---|---|---|
| `DATABASE_POOL_SIZE` | 20 | Steady-state pooled connections |
| `DATABASE_MAX_OVERFLOW` | 20 | Burst connections beyond pool |
| `DATABASE_POOL_TIMEOUT_SECONDS` | 30 | Wait before pool-exhaustion error |
| `DATABASE_POOL_RECYCLE_SECONDS` | 1800 | Recycle stale connections |
| `RATE_LIMIT_PER_MINUTE` | 120 | In-memory fixed window per client IP |
| `MAX_UPLOAD_BYTES` | 26214400 (25 MiB) | 413 rejection threshold for write bodies |
| `MAX_IMPORT_ROWS` | 100000 | Ingestion row cap |

## Pagination contract
| Endpoint | Default limit | Max | Offset |
|---|---|---|---|
| `GET /api/v1/anomalies` | 50 | 500 | `offset` |
| `GET /api/v1/audit` | 100 | 500 | `offset` |
| `GET /api/v1/cases` | 50 | 200 | `offset` |
| `GET /api/v1/erp/outbox` | 50 | 200 | `offset` |
| `GET /api/v1/imports` | 50 | 200 | `offset` |
| `GET /api/v1/reconciliation/runs` | 100 | 200 | `offset` |
| `GET /api/v1/reconciliation/results/{run_id}` | 50 | 500 | `offset` |

`GET /api/v1/dashboard/overview` returns aggregates (`COUNT`/`SUM`) — no pagination needed.

## Remaining capacity limits (honest)
- Single-process in-memory rate limiter: with N replicas the effective global
  limit is ~N× configured value; use a Redis token bucket for strict limits.
- No read replica / query cache; dashboard aggregates recompute per call —
  expect DB CPU to be the first ceiling under heavy polling.
- Production requires Postgres (`Settings.validate_production_contract`
  rejects SQLite) + explicit `CORS_ORIGINS` + API-key/service-account auth.
