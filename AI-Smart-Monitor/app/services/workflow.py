import hashlib
import json
from datetime import datetime, timezone

from app.core.audit import append_audit_event
from app.core.errors import DomainError
from app.models import Anomaly, ErpOutbox, InvestigationCase

ALLOWED = {
    "DETECTED": ["ACKNOWLEDGED", "INVESTIGATING", "FALSE_POSITIVE"],
    "ACKNOWLEDGED": ["INVESTIGATING", "RESOLVED"],
    "INVESTIGATING": ["RESOLVED", "ESCALATED"],
    "RESOLVED": ["VERIFIED", "REOPENED"],
    "VERIFIED": ["CLOSED", "REOPENED"],
    "ESCALATED": ["INVESTIGATING", "RESOLVED"],
    "REOPENED": ["INVESTIGATING"],
}


def transition(db, anomaly: Anomaly, status: str, actor: str = "api", reason: str | None = None, correlation_id: str | None = None):
    target = status.upper()
    if target not in ALLOWED.get(anomaly.status, []):
        raise DomainError("INVALID_TRANSITION", f"Invalid transition {anomaly.status} -> {target}", 409, {"allowed": ALLOWED.get(anomaly.status, [])})
    if target in {"RESOLVED", "FALSE_POSITIVE", "CLOSED"} and not (reason or "").strip():
        raise DomainError("RESOLUTION_REASON_REQUIRED", "A reason is required for terminal case decisions", 422)
    old = anomaly.status
    anomaly.status = target
    append_audit_event(db, actor=actor, action="ANOMALY_STATUS_CHANGED", entity_type="Anomaly", entity_id=str(anomaly.id), old_value={"status": old}, new_value={"status": target}, reason=reason, correlation_id=correlation_id, tenant_id=anomaly.tenant_id)
    db.commit()
    db.refresh(anomaly)
    return anomaly


def create_case(db, anomaly: Anomaly, actor: str = "api", assigned_to: str | None = None, correlation_id: str | None = None):
    case_key = f"CASE-{anomaly.id}"
    existing = db.query(InvestigationCase).filter_by(case_key=case_key).first()
    if existing:
        return existing, False
    case = InvestigationCase(anomaly_id=anomaly.id, case_key=case_key, assigned_to=assigned_to, status="OPEN", tenant_id=anomaly.tenant_id)
    db.add(case)
    append_audit_event(db, actor=actor, action="CASE_CREATED", entity_type="InvestigationCase", entity_id=case_key, new_value={"anomaly_id": anomaly.id, "assigned_to": assigned_to}, correlation_id=correlation_id, tenant_id=anomaly.tenant_id)
    db.commit()
    db.refresh(case)
    return case, True


def queue_erp(db, event_type: str, payload: dict, actor: str = "api", approval_reference: str | None = None, correlation_id: str | None = None, tenant_id: str = "default"):
    if event_type.upper() in {"ERP_WRITE", "SOURCE_MUTATION", "FINANCIAL_ADJUSTMENT"} and not approval_reference:
        raise DomainError("APPROVAL_REQUIRED", "ERP events require an approval reference", 409)
    canonical = json.dumps({"event_type": event_type, "payload": payload, "tenant_id": tenant_id}, sort_keys=True, default=str, separators=(",", ":"))
    idempotency_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    existing = db.query(ErpOutbox).filter_by(idempotency_key=idempotency_key).first()
    if existing:
        return existing, False
    event = ErpOutbox(event_type=event_type, idempotency_key=idempotency_key, payload={**payload, "approval_reference": approval_reference}, status="PENDING", tenant_id=tenant_id)
    db.add(event)
    append_audit_event(db, actor=actor, action="ERP_EVENT_QUEUED", entity_type="ErpOutbox", entity_id=idempotency_key, new_value={"event_type": event_type, "approval_reference": approval_reference}, correlation_id=correlation_id, tenant_id=tenant_id)
    db.commit()
    db.refresh(event)
    return event, True
