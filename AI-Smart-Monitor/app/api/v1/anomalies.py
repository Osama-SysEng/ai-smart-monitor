from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Anomaly
from app.services.workflow import transition
from app.core.identity import Identity, require_capability
router=APIRouter(prefix="/anomalies",tags=["anomalies"])
@router.get("")
def list_anomalies(status:str|None=None,severity:str|None=None,identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    q=db.query(Anomaly).filter(Anomaly.tenant_id == identity.tenant_id)
    if status:q=q.filter_by(status=status)
    if severity:q=q.filter_by(severity=severity)
    return q.order_by(Anomaly.id.desc()).limit(500).all()
@router.get("/{id}")
def get(id:int,identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    x=db.query(Anomaly).filter(Anomaly.id == id, Anomaly.tenant_id == identity.tenant_id).first()
    if not x: raise HTTPException(404,"Anomaly not found")
    return x
@router.post("/{id}/status/{status}")
def change(id:int,status:str,request: Request, reason: str | None = None, identity: Identity = Depends(require_capability("anomalies:write")),db:Session=Depends(get_db)):
    x=db.query(Anomaly).filter(Anomaly.id == id, Anomaly.tenant_id == identity.tenant_id).first()
    if not x: raise HTTPException(404,"Anomaly not found")
    try:return transition(db,x,status.upper(), actor=identity.actor, reason=reason, correlation_id=request.headers.get("X-Request-Id"))
    except ValueError as e:raise HTTPException(409,str(e))
