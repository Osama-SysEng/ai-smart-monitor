from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import ReconciliationRun,ReconciliationResult
from app.services.reconciliation import reconcile
router=APIRouter(prefix="/reconciliation",tags=["reconciliation"])
@router.post("/run")
def run(db:Session=Depends(get_db)): return reconcile(db)
@router.get("/runs")
def runs(db:Session=Depends(get_db)): return db.query(ReconciliationRun).order_by(ReconciliationRun.id.desc()).limit(100).all()
@router.get("/results/{run_id}")
def results(run_id:int,db:Session=Depends(get_db)): return db.query(ReconciliationResult).filter_by(run_id=run_id).all()
