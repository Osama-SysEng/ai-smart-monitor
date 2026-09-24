import React, { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Activity, AlertCircle, ArrowUpRight, BadgeCheck, BriefcaseBusiness, CircleDotDashed, Database, FileWarning, Filter, LoaderCircle, RefreshCw, Search, ShieldCheck, SlidersHorizontal, TriangleAlert } from "lucide-react";
import "./styles.css";

const API = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, headers: { "Content-Type": "application/json", "X-Request-Id": crypto.randomUUID(), ...(options.headers || {}) } });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.error?.message || body?.detail || `Request failed (${response.status})`);
  return body;
}

const severityClass = severity => ({ CRITICAL: "critical", HIGH: "high", MEDIUM: "medium", LOW: "low", INFO: "info" }[severity] || "info");
const displayNumber = value => new Intl.NumberFormat("ar-EG").format(Number(value || 0));
const displayMoney = value => new Intl.NumberFormat("ar-EG", { maximumFractionDigits: 2 }).format(Number(value || 0));

function MetricCard({ icon: Icon, label, value, tone, detail }) {
  return <article className={`metric-card ${tone}`}><div className="metric-icon"><Icon size={19} /></div><div><span>{label}</span><strong>{displayNumber(value)}</strong><small>{detail}</small></div></article>;
}

function App() {
  const [overview, setOverview] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [cases, setCases] = useState([]);
  const [health, setHealth] = useState(null);
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [query, setQuery] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);
  const [openingCase, setOpeningCase] = useState(null);

  const load = useCallback(async () => {
    setStatus("loading"); setError("");
    try {
      const [summary, anomaliesData, casesData, healthData] = await Promise.all([request("/dashboard/overview"), request("/anomalies?limit=100"), request("/cases?limit=50"), request("/health")]);
      setOverview(summary); setAnomalies(Array.isArray(anomaliesData) ? anomaliesData : []); setCases(Array.isArray(casesData) ? casesData : []); setHealth(healthData); setLastUpdated(new Date()); setStatus("ready");
    } catch (loadError) { setError(loadError.message || "تعذر تحميل مركز العمليات."); setStatus("error"); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visibleAnomalies = useMemo(() => anomalies.filter(item => {
    const matchesSeverity = severity === "ALL" || item.severity === severity;
    const text = `${item.transaction_id} ${item.item_code} ${item.type}`.toLowerCase();
    return matchesSeverity && text.includes(query.trim().toLowerCase());
  }), [anomalies, query, severity]);

  async function openCase(anomalyId) {
    setOpeningCase(anomalyId);
    try { const result = await request(`/cases/from-anomaly/${anomalyId}`, { method: "POST", body: JSON.stringify({}) }); setCases(current => result.created ? [result.case, ...current] : current); }
    catch (caseError) { setError(caseError.message || "تعذر فتح قضية التحقيق."); }
    finally { setOpeningCase(null); }
  }

  const critical = anomalies.filter(item => item.severity === "CRITICAL").length;
  const reconciliationRate = Math.max(0, Math.min(100, Number(overview?.reconciliation_rate || 0)));

  return <div className="app-shell" dir="rtl">
    <aside className="sidebar" aria-label="التنقل التشغيلي"><div className="brand"><span className="brand-mark"><Activity size={20} /></span><div><b>Smart Monitor</b><small>مركز الرقابة</small></div></div><nav><a className="active" href="#overview"><Activity size={17} />نظرة تشغيلية</a><a href="#anomalies"><TriangleAlert size={17} />الانحرافات <em>{displayNumber(anomalies.length)}</em></a><a href="#cases"><BriefcaseBusiness size={17} />قضايا التحقيق <em>{displayNumber(cases.length)}</em></a><a href="#integrations"><Database size={17} />التكاملات</a></nav><div className="safety-note"><ShieldCheck size={18} /><div><b>تحكم مضبوط</b><span>لا تُنفذ الكتابات الحساسة قبل اعتماد موثق.</span></div></div></aside>
    <main><header className="topbar"><div><p className="eyebrow">OPERATIONAL INTELLIGENCE / V4</p><h1>رؤية موحدة. قرارات موثقة.</h1><p className="subtitle">مطابقة حتمية، تحقيقات منظمة، وتنبيهات قابلة للتدقيق عبر مصادر البيانات.</p></div><div className="top-actions"><div className={`health ${health?.status === "ok" ? "healthy" : ""}`}><CircleDotDashed size={15} />{health?.status === "ok" ? "الخدمة سليمة" : "حالة الخدمة"}</div><button className="refresh" onClick={load} disabled={status === "loading"}><RefreshCw size={16} className={status === "loading" ? "spin" : ""} />تحديث البيانات</button></div></header>
      {status === "error" && <section className="error-state"><AlertCircle size={23} /><div><b>تعذر تحديث مركز العمليات</b><p>{error}</p></div><button onClick={load}>إعادة المحاولة</button></section>}
      <section id="overview" className="content-section"><div className="section-heading"><div><p className="eyebrow">PULSE</p><h2>نبض التشغيل</h2></div><span>{lastUpdated ? `آخر تحديث: ${lastUpdated.toLocaleTimeString("ar-EG")}` : "جارٍ الاتصال"}</span></div>{status === "loading" && !overview ? <div className="metrics loading-grid">{[1,2,3,4].map(item => <div key={item} className="skeleton metric-skeleton" />)}</div> : <div className="metrics"><MetricCard icon={Database} label="دفعات الاستيراد" value={overview?.imports} tone="blue" detail="مدخلات قابلة للتتبع" /><MetricCard icon={BadgeCheck} label="سجلات موحدة" value={overview?.facts} tone="teal" detail="حقائق جاهزة للمقارنة" /><MetricCard icon={TriangleAlert} label="انحرافات مفتوحة" value={overview?.anomalies} tone="amber" detail="تحتاج قرار تشغيل" /><MetricCard icon={ShieldCheck} label="حرجة" value={critical || overview?.critical} tone="rose" detail="أولوية فورية" /></div>}</section>
      <section className="signal-grid"><article className="panel reconciliation-panel"><div className="panel-title"><div><p className="eyebrow">RECONCILIATION</p><h2>صحة المطابقة</h2></div><span className="pill">حتمية</span></div><div className="score-row"><strong>{reconciliationRate.toFixed(1)}<small>%</small></strong><div><b>معدل التوافق</b><p>يحسب من نتائج المطابقة المسجلة، وليس تقديرًا من نموذج ذكاء اصطناعي.</p></div></div><div className="progress"><i style={{ width: `${reconciliationRate}%` }} /></div><div className="split-stats"><span><b>{Number(overview?.mismatch_rate || 0).toFixed(1)}%</b> نسبة عدم التطابق</span><span><b>{displayMoney(overview?.financial_impact)}</b> أثر مالي محتمل</span></div></article><article id="integrations" className="panel operations-panel"><div className="panel-title"><div><p className="eyebrow">CONTROL PLANE</p><h2>حالة التشغيل</h2></div><SlidersHorizontal size={20} /></div><div className="operation-row"><span><Database size={16} />طابور ERP</span><b>{displayNumber(overview?.erp_pending)} بانتظار الاعتماد</b></div><div className="operation-row"><span><TriangleAlert size={16} />التنبيهات</span><b>{displayNumber(overview?.alerts)} مسجلة</b></div><div className="operation-row"><span><BriefcaseBusiness size={16} />القضايا</span><b>{displayNumber(cases.length)} متابعة نشطة</b></div><p className="operator-caption">تظل إجراءات ERP الحساسة معطلة حتى يصل مرجع اعتماد قابل للتدقيق.</p></article></section>
      <section id="anomalies" className="content-section anomaly-section"><div className="section-heading"><div><p className="eyebrow">INVESTIGATE</p><h2>طابور الانحرافات</h2></div><span>{displayNumber(visibleAnomalies.length)} نتيجة معروضة</span></div><div className="toolbar"><div className="search"><Search size={17} /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="ابحث برقم العملية أو الصنف أو النوع" /></div><div className="filters"><Filter size={16} />{["ALL","CRITICAL","HIGH","MEDIUM","LOW"].map(level => <button key={level} onClick={() => setSeverity(level)} className={severity === level ? "selected" : ""}>{level === "ALL" ? "الكل" : level}</button>)}</div></div><div className="anomaly-list">{status === "loading" && !anomalies.length ? [1,2,3].map(item => <div key={item} className="skeleton row-skeleton" />) : visibleAnomalies.length ? visibleAnomalies.map(item => <article className="anomaly-row" key={item.id}><span className={`severity ${severityClass(item.severity)}`}>{item.severity}</span><div className="anomaly-main"><b>{item.type.replaceAll("_", " ")}</b><span>عملية {item.transaction_id} · صنف {item.item_code}</span></div><div className="impact"><small>الأثر المحتمل</small><b>{displayMoney(item.financial_impact)}</b></div><div className="state"><small>الحالة</small><b>{item.status}</b></div><button className="case-button" onClick={() => openCase(item.id)} disabled={openingCase === item.id}>{openingCase === item.id ? <LoaderCircle size={15} className="spin" /> : <ArrowUpRight size={15} />}{openingCase === item.id ? "جارٍ الفتح" : "فتح قضية"}</button></article>) : <div className="empty-state"><FileWarning size={26} /><b>لا توجد انحرافات تطابق هذا المرشح</b><span>جرّب تغيير مستوى الخطورة أو أزل نص البحث.</span></div>}</div></section>
      <section id="cases" className="content-section cases-section"><div className="section-heading"><div><p className="eyebrow">CASEWORK</p><h2>سجل التحقيقات</h2></div><span>يمنع النظام إنشاء قضية ثانية للانحراف نفسه.</span></div><div className="case-grid">{cases.length ? cases.slice(0,6).map(item => <article className="case-card" key={item.id}><span>{item.case_key || `CASE-${item.id}`}</span><b>{item.status}</b><small>المكلف: {item.assigned_to || "غير معيّن"}</small></article>) : <div className="empty-state wide"><BriefcaseBusiness size={26} /><b>لم تُفتح أي قضايا تحقيق بعد</b><span>اختر انحرافًا من الطابور لفتح قضية موثقة.</span></div>}</div></section>
    </main>
  </div>;
}

createRoot(document.getElementById("root")).render(<App />);
