# Implementation Map

## Deterministic Core
`app/services/ingestion.py` → import, hashing, mapping, validation.
`app/services/reconciliation.py` → pairwise comparisons and mismatch facts.
`app/services/severity.py` → severity scoring.
`app/services/workflow.py` → lifecycle transitions.
`app/services/ai.py` → interpretation only.

## Data Model
- data_imports
- source_facts
- reconciliation_runs
- reconciliation_results
- anomalies
- alerts
- investigation_cases
- erp_outbox
- audit_logs

## Production extension points
1. Replace `MockProvider` with OpenAI/Gemini/Claude adapters.
2. Add authentication/RBAC middleware.
3. Move jobs to Celery/RQ/Arq with Redis.
4. Add real ERP connector and read-back verification.
5. Add database migrations with Alembic.
6. Add immutable audit storage/WORM policy.
7. Add branch/department master-data resolution.
8. Add advanced pattern detection and rolling statistics.
