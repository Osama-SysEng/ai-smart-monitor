"""Durable outbox delivery with idempotent claims and a tenant-scoped circuit breaker."""
from datetime import datetime, timedelta, timezone

from app.core.audit import append_audit_event
from app.core.config import settings
from app.models import DeliveryAttempt, ErpOutbox, IntegrationCircuit
from app.services.erp import ERPAdapter


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value


def _retry_at(attempts: int) -> datetime:
    seconds = min(settings.erp_base_retry_seconds * (2 ** max(0, attempts - 1)), 86_400)
    return utcnow() + timedelta(seconds=seconds)


def _circuit(db, tenant_id: str) -> IntegrationCircuit:
    circuit = db.query(IntegrationCircuit).filter_by(target="erp", tenant_id=tenant_id).first()
    if not circuit:
        circuit = IntegrationCircuit(target="erp", tenant_id=tenant_id)
        db.add(circuit)
        db.flush()
    return circuit


def _circuit_open(circuit: IntegrationCircuit) -> bool:
    return bool(_aware(circuit.opened_until) and _aware(circuit.opened_until) > utcnow())


def _record_attempt(db, event: ErpOutbox, outcome: str, response: dict) -> None:
    db.add(DeliveryAttempt(
        outbox_id=event.id,
        tenant_id=event.tenant_id,
        attempt_number=event.attempts,
        outcome=outcome,
        status_code=response.get("http_status"),
        error_category=response.get("error_category"),
        detail=(response.get("error") or response.get("body") or "")[:500] or None,
    ))


def deliver_due(db, *, tenant_id: str, adapter: ERPAdapter | None = None, limit: int = 25, actor: str = "worker", correlation_id: str | None = None) -> dict:
    """Claim and deliver a bounded batch without executing duplicate outbox items."""
    adapter = adapter or ERPAdapter()
    circuit = _circuit(db, tenant_id)
    if _circuit_open(circuit):
        return {"status": "CIRCUIT_OPEN", "delivered": 0, "opened_until": _aware(circuit.opened_until).isoformat()}
    now = utcnow()
    candidates = db.query(ErpOutbox).filter(
        ErpOutbox.tenant_id == tenant_id,
        ErpOutbox.status.in_(["PENDING", "RETRY"]),
        (ErpOutbox.next_retry_at.is_(None)) | (ErpOutbox.next_retry_at <= now),
    ).order_by(ErpOutbox.id).limit(limit).all()
    delivered = retried = dead_lettered = blocked = 0
    for event in candidates:
        claim = db.query(ErpOutbox).filter(ErpOutbox.id == event.id, ErpOutbox.status.in_(["PENDING", "RETRY"])).update({"status": "PROCESSING", "locked_until": now + timedelta(minutes=5)}, synchronize_session=False)
        if not claim:
            continue
        db.commit()
        db.refresh(event)
        event.attempts += 1
        response = adapter.push(event.event_type, event.payload, event.idempotency_key)
        event.last_status_code = response.get("http_status")
        if response.get("status") == "SENT":
            event.status = "SENT"
            event.processed_at = utcnow()
            event.next_retry_at = None
            circuit.consecutive_failures = 0
            circuit.opened_until = None
            _record_attempt(db, event, "SENT", response)
            append_audit_event(db, actor=actor, action="ERP_DELIVERED", entity_type="ErpOutbox", entity_id=str(event.id), correlation_id=correlation_id, tenant_id=tenant_id)
            delivered += 1
        elif response.get("status") == "NOT_CONFIGURED":
            event.status = "BLOCKED"
            event.last_error = "ERP integration is not configured"
            _record_attempt(db, event, "BLOCKED", response)
            blocked += 1
        else:
            event.last_error = (response.get("error") or response.get("body") or "ERP delivery failed")[:500]
            retryable = bool(response.get("retryable"))
            circuit.consecutive_failures += 1
            if circuit.consecutive_failures >= settings.erp_circuit_failure_threshold:
                circuit.opened_until = utcnow() + timedelta(seconds=settings.erp_circuit_cooldown_seconds)
            if retryable and event.attempts < settings.erp_max_attempts:
                event.status = "RETRY"
                event.next_retry_at = _retry_at(event.attempts)
                _record_attempt(db, event, "RETRY", response)
                retried += 1
            else:
                event.status = "DEAD_LETTER"
                event.next_retry_at = None
                _record_attempt(db, event, "DEAD_LETTER", response)
                append_audit_event(db, actor=actor, action="ERP_DEAD_LETTERED", entity_type="ErpOutbox", entity_id=str(event.id), reason=event.last_error, correlation_id=correlation_id, tenant_id=tenant_id)
                dead_lettered += 1
        event.locked_until = None
        circuit.updated_at = utcnow()
        db.commit()
    return {"status": "COMPLETED", "delivered": delivered, "retried": retried, "dead_lettered": dead_lettered, "blocked": blocked}
