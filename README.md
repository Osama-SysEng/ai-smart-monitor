# The Smart Monitor — المراقب الذكي

منصة رقابة تشغيلية ذكية متعددة المصادر. هذه النسخة تحول الهيكل البرمجي المنظم المستخلص من مشروع Al-La'eeb إلى منصة مستقلة باسم **The Smart Monitor** وفق المواصفات التنفيذية المرسلة.

## Pipeline
Data Sources → Ingestion → Column Mapping → Normalization → Validation → Canonical Store → Reconciliation → Anomaly Detection → Severity/Financial Impact → Evidence → AI Interpretation → Alerts → Case Workflow → ERP Outbox → Verification → Audit.

## مبدأ أساسي
المطابقة والحسابات المالية **Deterministic** داخل Python/SQL. طبقة AI تفسيرية فقط، ولا تملك صلاحية تعديل البيانات أو تجاوز النتائج القطعية.

## التشغيل
```bash
cp .env.example .env
docker compose up --build
```
API: http://localhost:8000/docs  
Dashboard: http://localhost:5173

للتشغيل المحلي بدون Docker:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Demo
```bash
python scripts/demo_seed.py
curl -X POST http://localhost:8000/api/v1/reconciliation/run
```

أو افتح Dashboard بعد تشغيل النظام.

## ما تم تضمينه
- Excel/CSV ingestion
- file hash + record deduplication
- synonym/fuzzy-ready column mapping
- canonical transaction/source facts
- validation + quarantine status
- configurable YAML reconciliation rules
- multi-source pairwise reconciliation
- deterministic anomaly detectors
- severity scoring + financial impact
- anomaly fingerprint/deduplication
- alert lifecycle + routing
- Telegram adapter
- AI provider abstraction + safe mock provider
- ERP outbox + retry/verification skeleton
- append-only audit events
- dashboard API
- React dashboard
- PostgreSQL/Redis/Docker
- Prometheus configuration
- tests and sample datasets
