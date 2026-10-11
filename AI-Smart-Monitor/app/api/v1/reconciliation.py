from fastapi import APIRouter,Depends,Query,Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.identity import Identity, require_capability
from app.models import ReconciliationRun,ReconciliationResult
from app.services.reconciliation import reconcile
router=APIRouter(prefix="/reconciliation",tags=["reconciliation"])
@router.post("/run")
def run(request: Request, identity: Identity = Depends(require_capability("reconciliation:run")),db:Session=Depends(get_db)):
    return reconcile(db, correlation_id=request.headers.get("X-Request-Id"), tenant_id=identity.tenant_id)
@router.get("/runs")
def runs(limit: int = Query(default=100, ge=1, le=200),offset: int = Query(default=0, ge=0),identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    return db.query(ReconciliationRun).order_by(ReconciliationRun.id.desc()).offset(offset).limit(limit).all()
@router.get("/results/{run_id}")
def results(run_id:int,limit: int = Query(default=50, ge=1, le=500),offset: int = Query(default=0, ge=0),identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    return db.query(ReconciliationResult).filter_by(run_id=run_id).offset(offset).limit(limit).all()
