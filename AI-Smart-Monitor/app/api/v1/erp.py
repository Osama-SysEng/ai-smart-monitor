from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import append_audit_event
from app.db.session import get_db
from app.models import ErpOutbox
from app.services.workflow import queue_erp
from app.core.identity import Identity, require_capability

router = APIRouter(prefix="/erp", tags=["erp"])


class Event(BaseModel):
    event_type: str = Field(min_length=3, max_length=100)
    payload: dict = Field(default_factory=dict)
    approval_reference: str | None = Field(default=None, max_length=150)


@router.post("/outbox")
def add(event: Event, request: Request, identity: Identity = Depends(require_capability("erp:write")), db: Session = Depends(get_db)):
    item, created = queue_erp(db, event.event_type, event.payload, actor=identity.actor, approval_reference=event.approval_reference, correlation_id=request.headers.get("X-Request-Id"), tenant_id=identity.tenant_id)
    return {"event": item, "created": created}


@router.get("/outbox")
def list_outbox(limit: int = Query(default=50, ge=1, le=200), status: str | None = None, identity: Identity = Depends(require_capability("erp:read")), db: Session = Depends(get_db)):
    query = db.query(ErpOutbox).filter(ErpOutbox.tenant_id == identity.tenant_id)
    if status:
        query = query.filter(ErpOutbox.status == status.upper())
    return query.order_by(ErpOutbox.id.desc()).limit(limit).all()


@router.post("/outbox/{event_id}/retry")
def retry(event_id: int, request: Request, identity: Identity = Depends(require_capability("erp:write")), db: Session = Depends(get_db)):
    item = db.query(ErpOutbox).filter(ErpOutbox.id == event_id, ErpOutbox.tenant_id == identity.tenant_id).first()
    if not item:
        raise HTTPException(404, "Outbox event not found")
    item.status = "PENDING"
    item.last_error = None
    append_audit_event(db, actor=identity.actor, action="ERP_EVENT_REQUEUED", entity_type="ErpOutbox", entity_id=item.id.__str__(), correlation_id=request.headers.get("X-Request-Id"), tenant_id=identity.tenant_id)
    db.commit()
    return item
