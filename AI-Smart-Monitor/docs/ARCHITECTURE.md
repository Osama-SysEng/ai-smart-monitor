# Smart Monitor Apex Architecture

## Mission
Autonomous business-operations intelligence platform. Deterministic systems own facts, calculations, authorization and financial state. Agents own interpretation, investigation, prioritization and bounded recommendations.

## Pipeline
Sources -> Ingestion -> Mapping -> Validation -> Canonical Facts -> Reconciliation -> Anomaly -> Evidence -> Agent Investigation -> Root Cause -> Risk/Policy -> Human Approval or Autonomous Low-Risk Action -> ERP Outbox -> External ERP -> Read-back Verification -> Audit -> Feedback Memory.

## Agents
- Monitoring Agent: triage and evidence synthesis.
- Root Cause Agent: ranked hypotheses.
- Forecast Agent: recurrence/risk signal.
- Future extension: Finance, Procurement, Warehouse, Executive, Audit agents.

## Autonomy policy
- Read/analysis: autonomous.
- Notifications/case creation: autonomous.
- Source mutation / financial adjustment / ERP write / high-severity actions: approval required.
- Every action must be idempotent and auditable.

## Reliability
- File and record deduplication.
- Fingerprint anomaly deduplication.
- Outbox pattern.
- Retry-ready ERP boundary.
- Health/readiness endpoints.
- Rate limiting outside development.
- Hash-linked audit metadata.
- Deterministic financial impact.

## AI boundary
LLM receives structured evidence only. LLM cannot authoritatively change quantities, costs, source facts, permissions or severity.
