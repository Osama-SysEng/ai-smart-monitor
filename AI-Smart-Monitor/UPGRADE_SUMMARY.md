# AI-Smart-Monitor Enterprise Upgrade

## What changed

This upgrade strengthens the monitor from a thin operational dashboard into a controlled investigation platform. The backend now uses production-aware configuration validation, correlation identifiers, structured API errors, bounded uploads, strict import validation, quarantine status, duplicate protection, idempotent investigation cases, approval references for sensitive ERP events, and hash-linked audit event conventions.

The reconciliation engine now reads configured source pairs and thresholds rather than relying on fixed pairs in the service. It creates dashboard alerts in `PENDING_DISPATCH` state instead of sending external notifications from the deterministic comparison loop. The React dashboard has been rebuilt as a responsive operator console with loading, failure, empty, filtering, search, case-opening, and integration-control states.

## Verification completed

| Check | Result |
|---|---|
| Python test suite | `10 passed` |
| Frontend production build | Passed with Vite |
| Import quarantine and deduplication | Covered by tests |
| Case and ERP idempotency/approval gates | Covered by tests |
| Request correlation and structured validation errors | Covered by HTTP contract tests |
| Configurable reconciliation and dashboard-only alert queue | Covered by tests |

## Important operational boundary

External ERP writes, Telegram delivery, production AI providers, and any production database remain intentionally unconfigured. Configure them only through deployment secrets and documented approval workflows. Read `docs/PRODUCTION_READINESS.md` before a staging deployment.

## Local verification

```bash
pip install -r requirements.txt
pytest -q
cd frontend && pnpm install && pnpm build
```

For local development, start the API only after setting a development `.env`; do not use production secrets in a local environment.
