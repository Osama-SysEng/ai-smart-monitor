# PRD — AI-Smart-Monitor (المراقب الذكي)
## 1. نظرة عامة
- منصة رقابة تشغيلية متعددة المصادر: استيراد ← مطابقة حتمية ← شذوذ ← تنبيهات ← قضايا ← ERP outbox ← تدقيق.
- المطابقة والحسابات المالية Deterministic في Python/SQL.
- AI تفسيري فقط، بلا صلاحية تعديل البيانات أو تجاوز الحتمي.
- Backend: FastAPI (`app/main.py`) ببادئة `/api/v1`. Dashboard: React (`:5173`).
## 2. المستخدمون
1. مشغّل — استيراد ملفات وتشغيل مطابقة.
2. محقق — مراجعة الشذوذ والتحقيق AI.
3. معتمد — قضايا وERP outbox.
4. مدقق — سجل audit append-only.
5. حساب خدمة — `service-accounts` + `sessions` قابلة للإبطال.
## 3. الميزات الأساسية (قابلة للاختبار)
1. استيراد Excel/CSV (hash + dedup) + قائمة الاستيرادات.
2. تشغيل مطابقة + قائمة runs + نتائج run.
3. عرض الشذوذ + تفصيل شذوذ + تغيير حالته.
4. تحقيق AI في شذوذ + الاستعلام عن سياسة إجراء.
5. لوحة `dashboard/overview` المجمعة.
6. إنشاء قضية من شذوذ + قائمة القضايا.
7. دورة حياة التنبيهات (lifecycle + routing).
8. ERP outbox: إنشاء + قائمة + إعادة retry (مع circuit-breaker).
9. سجل audit للأحداث (append-only).
10. فحوصات health/ready + مقاييس operations + جلسات آمنة.
## 4. الـAPI endpoints الحقيقية (من الكود فقط)
- `POST /api/v1/imports` / `GET /api/v1/imports`
- `POST /api/v1/reconciliation/run` / `GET /api/v1/reconciliation/runs`
- `GET /api/v1/reconciliation/results/{run_id}`
- `GET /api/v1/anomalies` / `GET /api/v1/anomalies/{id}`
- `POST /api/v1/anomalies/{id}/status/{status}`
- `POST /api/v1/intelligence/anomalies/{anomaly_id}/investigate`
- `GET /api/v1/intelligence/anomalies/{anomaly_id}/policy/{action}`
- `GET /api/v1/dashboard/overview`
- `POST /api/v1/cases/from-anomaly/{anomaly_id}` / `GET /api/v1/cases`
- `POST /api/v1/erp/outbox` / `GET /api/v1/erp/outbox`
- `POST /api/v1/erp/outbox/{event_id}/retry`
- `GET /api/v1/audit`
- `POST /api/v1/security/service-accounts` / `POST /api/v1/security/sessions`
- `POST /api/v1/security/sessions/current/revoke`
- `GET /api/v1/health` / `GET /api/v1/ready` / `GET /api/v1/operations/metrics` / `GET /`
## 5. بيانات الدخول/الإعداد للاختبار
- انسخ `.env.example` إلى `.env`.
- `AI_PROVIDER=mock` افتراضيًا (آمن بدون مفاتيح).
- `DATABASE_URL` (postgres) أو sqlite محليًا + `SECRET_KEY/SESSION_SECRET`.
- التشغيل: `docker compose up --build` (API `:8000/docs`).
- الديمو: `python scripts/demo_seed.py` ثم `POST /api/v1/reconciliation/run`.
- الحدود: `MAX_UPLOAD_BYTES` و`MAX_IMPORT_ROWS=100000` و`RATE_LIMIT_PER_MINUTE=120`.
- الاختبارات: `pytest tests/ -v` + مجموعات `data/` النموذجية.
## 6. خارج النطاق (mocked/simulated — صراحة)
- AI بمزود `mock` — لا يعدّل بيانات ولا يتجاوز الحتمي.
- Telegram adapter يحتاج `TELEGRAM_BOT_TOKEN/CHAT_ID` حقيقيين.
- ERP (`ERP_BASE_URL/API_KEY`) غير موجود في الاختبار — تُختبر الـoutbox والـretry فقط.
- قواعد المطابقة YAML قابلة للضبط؛ لا نتائج سحرية.
- التشفير/الاحتفاظ/العزل الكامل مؤجل لمراجعة الإنتاج.
