import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def _canonical(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))


def append_audit_event(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    reason: str | None = None,
    correlation_id: str | None = None,
    tenant_id: str = "default",
) -> AuditLog:
    previous = db.query(AuditLog).filter_by(tenant_id=tenant_id).order_by(AuditLog.id.desc()).first()
    previous_hash = previous.event_hash if previous else None
    payload = {
        "actor": actor,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "correlation_id": correlation_id,
        "tenant_id": tenant_id,
        "previous_hash": previous_hash,
    }
    event_hash = hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()
    event = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        correlation_id=correlation_id,
        tenant_id=tenant_id,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )
    db.add(event)
    return event
