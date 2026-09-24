from fastapi import APIRouter,Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import DataImport,SourceFact,Anomaly,Alert,ErpOutbox,ReconciliationResult
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/overview")
def overview(db:Session=Depends(get_db)):
    total=db.query(func.count(ReconciliationResult.id)).scalar() or 0
    mism=db.query(func.count(ReconciliationResult.id)).filter(ReconciliationResult.status=="MISMATCH").scalar() or 0
    impact=db.query(func.sum(Anomaly.financial_impact)).scalar() or 0
    return {"imports":db.query(func.count(DataImport.id)).scalar() or 0,"facts":db.query(func.count(SourceFact.id)).scalar() or 0,
      "anomalies":db.query(func.count(Anomaly.id)).scalar() or 0,"critical":db.query(func.count(Anomaly.id)).filter_by(severity="CRITICAL").scalar() or 0,
      "alerts":db.query(func.count(Alert.id)).scalar() or 0,"erp_pending":db.query(func.count(ErpOutbox.id)).filter_by(status="PENDING").scalar() or 0,
      "reconciliation_rate":round((1-mism/total)*100,2) if total else 100,"mismatch_rate":round(mism/total*100,2) if total else 0,
      "financial_impact":float(impact)}
