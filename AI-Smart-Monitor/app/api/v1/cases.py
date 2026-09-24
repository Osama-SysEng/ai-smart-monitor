from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Anomaly, InvestigationCase
from app.core.identity import Identity, require_capability
from app.services.workflow import create_case

router = APIRouter(prefix="/cases", tags=["cases"])


class CaseCreateRequest(BaseModel):
    assigned_to: str | None = Field(default=None, max_length=150)


@router.post("/from-anomaly/{anomaly_id}")
def create(anomaly_id: int, body: CaseCreateRequest, request: Request, identity: Identity = Depends(require_capability("cases:write")), db: Session = Depends(get_db)):
    anomaly = db.query(Anomaly).filter(Anomaly.id == anomaly_id, Anomaly.tenant_id == identity.tenant_id).first()
    if not anomaly:
        raise HTTPException(404, "Anomaly not found")
    case, created = create_case(db, anomaly, actor=identity.actor, assigned_to=body.assigned_to, correlation_id=request.headers.get("X-Request-Id"))
    return {"case": case, "created": created}


@router.get("")
def list_cases(limit: int = Query(default=50, ge=1, le=200), status: str | None = None, identity: Identity = Depends(require_capability("cases:read")), db: Session = Depends(get_db)):
    query = db.query(InvestigationCase).filter(InvestigationCase.tenant_id == identity.tenant_id)
    if status:
        query = query.filter(InvestigationCase.status == status.upper())
    return query.order_by(InvestigationCase.id.desc()).limit(limit).all()
