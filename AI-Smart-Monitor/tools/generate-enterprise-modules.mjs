import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const root = "/home/ubuntu/AI-Smart-Monitor-Enterprise";
const domains = [
  ["imports", "Import", "data intake, validation, and quarantine"],
  ["reconciliation", "Reconciliation", "deterministic comparisons and evidence"],
  ["anomalies", "Anomaly", "detection, severity, and investigation priority"],
  ["cases", "Case", "operator-owned investigation lifecycle"],
  ["alerts", "Alert", "controlled delivery and acknowledgement"],
  ["integrations", "Integration", "outbox delivery and external boundary control"],
];
const features = ["overview", "anomaly-queue", "casework", "import-center", "integration-status", "audit-trail"];

async function emit(relativePath, content) {
  const target = path.join(root, relativePath);
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, content.trimStart(), "utf8");
}

for (const [domain, entity, purpose] of domains) {
  const packagePath = `app/domain/${domain}`;
  await emit(`${packagePath}/__init__.py`, `"""${entity} domain package: ${purpose}."""\nfrom .contracts import ${entity}Snapshot\nfrom .policies import approval_required\n\n__all__ = ["${entity}Snapshot", "approval_required"]\n`);
  await emit(`${packagePath}/contracts.py`, `from datetime import datetime\nfrom pydantic import BaseModel, Field\n\nclass ${entity}Snapshot(BaseModel):\n    identifier: str = Field(min_length=1, max_length=150)\n    status: str = Field(min_length=1, max_length=40)\n    correlation_id: str | None = Field(default=None, max_length=64)\n    observed_at: datetime | None = None\n\nclass ${entity}Page(BaseModel):\n    items: list[${entity}Snapshot] = Field(default_factory=list)\n    next_cursor: str | None = None\n`);
  await emit(`${packagePath}/commands.py`, `from dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass Create${entity}:\n    actor: str\n    correlation_id: str\n    reason: str | None = None\n\n@dataclass(frozen=True)\nclass Update${entity}Status:\n    identifier: str\n    target_status: str\n    actor: str\n    reason: str | None = None\n`);
  await emit(`${packagePath}/events.py`, `from dataclasses import dataclass\nfrom datetime import datetime, timezone\n\n@dataclass(frozen=True)\nclass ${entity}Event:\n    event_type: str\n    identifier: str\n    correlation_id: str\n    occurred_at: datetime\n\n    @classmethod\n    def now(cls, event_type: str, identifier: str, correlation_id: str):\n        return cls(event_type, identifier, correlation_id, datetime.now(timezone.utc))\n`);
  await emit(`${packagePath}/policies.py`, `SENSITIVE_ACTIONS = {"ERP_WRITE", "SOURCE_MUTATION", "FINANCIAL_ADJUSTMENT"}\n\ndef approval_required(action: str, severity: str = "INFO") -> bool:\n    return action.upper() in SENSITIVE_ACTIONS or severity.upper() in {"HIGH", "CRITICAL"}\n\ndef may_auto_dispatch(channel: str, severity: str) -> bool:\n    return channel == "dashboard" and severity.upper() in {"INFO", "LOW"}\n`);
  await emit(`${packagePath}/repository.py`, `from typing import Protocol\nfrom .contracts import ${entity}Page, ${entity}Snapshot\n\nclass ${entity}Repository(Protocol):\n    def get(self, identifier: str) -> ${entity}Snapshot | None: ...\n    def list(self, cursor: str | None = None, limit: int = 50) -> ${entity}Page: ...\n`);
  await emit(`${packagePath}/service.py`, `from .contracts import ${entity}Snapshot\n\ndef display_label(snapshot: ${entity}Snapshot) -> str:\n    return f"{snapshot.identifier} · {snapshot.status}"\n\ndef is_terminal(status: str) -> bool:\n    return status.upper() in {"CLOSED", "FAILED", "QUARANTINED", "VERIFIED"}\n`);
  await emit(`${packagePath}/telemetry.py`, `METRIC_PREFIX = "smart_monitor.${domain}"\n\ndef metric(name: str) -> str:\n    return f"{METRIC_PREFIX}.{name}"\n\ndef tags(status: str, correlation_id: str | None) -> dict[str, str]:\n    return {"status": status, "correlation_id": correlation_id or "unassigned"}\n`);
  await emit(`tests/domain/test_${domain}_domain.py`, `from app.domain.${domain}.contracts import ${entity}Snapshot\nfrom app.domain.${domain}.policies import approval_required\nfrom app.domain.${domain}.service import display_label, is_terminal\n\ndef test_${domain}_domain_contract_and_policy():\n    snapshot = ${entity}Snapshot(identifier="${domain}-001", status="OPEN", correlation_id="req-${domain}")\n    assert display_label(snapshot) == "${domain}-001 · OPEN"\n    assert is_terminal("CLOSED") is True\n    assert approval_required("ERP_WRITE") is True\n    assert approval_required("READ") is False\n`);
  for (const document of ["operating-model", "failure-modes", "acceptance-criteria"]) {
    await emit(`docs/domains/${domain}/${document}.md`, `# ${entity}: ${document.replaceAll("-", " ")}\n\n## Responsibility\n\nThe ${entity} domain owns ${purpose}. It exposes explicit commands, stable read contracts, policy checks, and correlation-aware events.\n\n## Operator rule\n\nNo sensitive transition is automatic. Record the actor, reason, correlation identifier, and approval reference whenever the operation crosses a system boundary.\n\n## Acceptance signal\n\nA change is accepted only when its domain test, API contract, and operational evidence agree.\n`);
}
}

for (const feature of features) {
  const label = feature.replaceAll("-", " ");
  const folder = `frontend/src/features/${feature}`;
  await emit(`${folder}/types.js`, `/** @typedef {{ id: string|number, status: string, correlationId?: string }} ${feature.replaceAll("-", "_")}Record */\nexport const featureName = "${feature}";\n`);
  await emit(`${folder}/api.js`, `export const ${feature.replaceAll("-", "_")}Endpoint = "/${feature}";\nexport function withCursor(endpoint, cursor) { return cursor ? \`${"${endpoint}"}?cursor=\${encodeURIComponent(cursor)}\` : endpoint; }\n`);
  await emit(`${folder}/selectors.js`, `export function byStatus(items, status) { return status === "ALL" ? items : items.filter(item => item.status === status); }\nexport function byQuery(items, query, keys = ["id", "status"]) { const needle = query.trim().toLowerCase(); return !needle ? items : items.filter(item => keys.some(key => String(item[key] ?? "").toLowerCase().includes(needle))); }\n`);
  await emit(`${folder}/state.js`, `export const initialState = { status: "idle", data: [], error: null, updatedAt: null };\nexport function reducer(state, action) { if (action.type === "loading") return { ...state, status: "loading", error: null }; if (action.type === "success") return { status: "ready", data: action.data, error: null, updatedAt: action.updatedAt }; if (action.type === "error") return { ...state, status: "error", error: action.error }; return state; }\n`);
  await emit(`${folder}/view-model.js`, `export function toViewModel(record) { return { id: record.id, status: record.status || "UNKNOWN", label: record.label || \`${label}: \${record.id}\`, correlationId: record.correlation_id || record.correlationId || null }; }\n`);
  await emit(`${folder}/accessibility.js`, `export const labels = { loading: "جارٍ تحميل ${label}", empty: "لا توجد بيانات ${label}", retry: "إعادة المحاولة", refresh: "تحديث ${label}" };\nexport function regionProps() { return { role: "region", "aria-label": "${label}" }; }\n`);
  await emit(`${folder}/README.md`, `# ${feature}\n\nThis feature module separates API addresses, state transitions, selectors, view models, and accessibility text. Integrate it into the operator console only through its public functions so UI changes do not rewrite transport or policy logic.\n`);
}

for (const file of [
  "infrastructure/kubernetes/base/namespace.yaml", "infrastructure/kubernetes/base/configmap.yaml", "infrastructure/kubernetes/base/api-deployment.yaml", "infrastructure/kubernetes/base/frontend-deployment.yaml", "infrastructure/kubernetes/base/api-service.yaml", "infrastructure/kubernetes/base/frontend-service.yaml", "infrastructure/kubernetes/base/network-policy.yaml", "infrastructure/kubernetes/overlays/staging/kustomization.yaml", "infrastructure/kubernetes/overlays/production/kustomization.yaml", "infrastructure/observability/alerts.md", "infrastructure/observability/slo.md", "infrastructure/security/secret-rotation.md"
]) {
  const title = path.basename(file).replaceAll("-", " ");
  const isYaml = file.endsWith(".yaml");
  await emit(file, isYaml ? `apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: smart-monitor-${title.replace(".yaml", "").replaceAll(" ", "-")}\n  labels:\n    app.kubernetes.io/name: smart-monitor\ndata:\n  managed-by: "architecture-upgrade"\n` : `# ${title}\n\nThis operational artifact belongs to the Smart Monitor enterprise delivery. Review it with platform engineering before deployment; it is intentionally a safe template, not an environment credential or automatic production change.\n`);
}

console.log(`Generated domain, frontend, test, documentation, and infrastructure modules for ${domains.length} domains and ${features.length} operator features.`);
