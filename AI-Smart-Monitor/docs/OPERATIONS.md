# Operations Runbook

1. Copy `.env.example` to `.env`.
2. Set production `DATABASE_URL`, `REDIS_URL`, secrets, CORS and API key.
3. Set `REQUIRE_API_KEY=true` in production.
4. Configure `AI_PROVIDER=openai` and `OPENAI_API_KEY` if LLM analysis is desired.
5. Configure ERP endpoint only after idempotency + read-back verification contract is available.
6. Run migrations when Alembic is introduced; current bootstrap creates missing tables only.
7. Monitor `/api/v1/health`, `/api/v1/ready`, Prometheus metrics and application logs.
8. Keep Telegram secrets outside source control.
