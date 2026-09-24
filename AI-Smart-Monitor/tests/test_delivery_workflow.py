"""Durability contracts for ERP outbox delivery."""
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models import ErpOutbox
from app.services.delivery import deliver_due
from app.services.workflow import queue_erp


class SendingAdapter:
    def push(self, *_args):
        return {"status": "SENT", "http_status": 202, "retryable": False}


class FailingAdapter:
    def push(self, *_args):
        return {"status": "FAILED", "http_status": 503, "retryable": True, "error_category": "REMOTE_SERVER", "error": "temporary outage"}


def test_outbox_delivery_records_success_and_preserves_tenant(db):
    event, _ = queue_erp(db, "ERP_WRITE", {"reference": "A-1"}, approval_reference="APR-A", tenant_id="tenant-a")
    result = deliver_due(db, tenant_id="tenant-a", adapter=SendingAdapter())
    db.refresh(event)
    assert result["delivered"] == 1
    assert event.status == "SENT"
    assert event.tenant_id == "tenant-a"


def test_outbox_failure_schedules_retry_then_opens_circuit(db):
    original_threshold = settings.erp_circuit_failure_threshold
    settings.erp_circuit_failure_threshold = 1
    try:
        event, _ = queue_erp(db, "ERP_WRITE", {"reference": "B-1"}, approval_reference="APR-B", tenant_id="tenant-b")
        result = deliver_due(db, tenant_id="tenant-b", adapter=FailingAdapter())
        db.refresh(event)
        assert result["retried"] == 1
        assert event.status == "RETRY"
        assert event.next_retry_at > datetime.now(timezone.utc).replace(tzinfo=None)
        blocked = deliver_due(db, tenant_id="tenant-b", adapter=FailingAdapter())
        assert blocked["status"] == "CIRCUIT_OPEN"
    finally:
        settings.erp_circuit_failure_threshold = original_threshold
