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
def runs(limit: int = Query(default=100, ge=1, le=200),identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    return db.query(ReconciliationRun).order_by(ReconciliationRun.id.desc()).limit(limit).all()
@router.get("/results/{run_id}")
def results(run_id:int,limit: int = Query(default=500, ge=1, le=1000),identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    return db.query(ReconciliationResult).filter_by(run_id=run_id).limit(limit).all()
