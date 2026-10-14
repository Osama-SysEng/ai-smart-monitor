# Structured Logging (Smart Monitor)

Stdlib-only JSON logging via `app/core/logging_utils.py` (no new dependencies).

## One line per request

`request_controls` in `app/main.py` echoes/propagates `X-Request-ID` and emits a
single access line per request (including 413/401/429 rejections):

```json
{"timestamp": "...", "level": "info", "service": "smart-monitor",
 "env": "test", "version": "dev", "request_id": "req-root-001",
 "event": "http.access", "message": "http.access: GET / -> 200 in 1.2ms",
 "http.method": "GET", "http.path": "/",
 "http.status_code": 200, "duration_ms": 1.2}
```

## Env (.env.example)

| Var | Purpose | Default |
| --- | ------- | ------- |
| `SERVICE_NAME` | `service` field | `smart-monitor` |
| `LOG_LEVEL` | min level | `INFO` (`debug` outside production) |
| `GIT_SHA` | `version` field | `dev` |
| `ENVIRONMENT` | `env` field | `development` |

## Rules

- Never log secrets — keys containing `password/token/secret/api_key/authorization/cookie/...` are redacted as `***`.
- No `print()` in runtime code (`app/`); use `get_logger(__name__)` + `log_access(...)`.
- Correlate with `X-Request-ID` (also in error bodies as `request_id`).
