from fastapi import APIRouter,Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.identity import Identity, require_capability
from app.models import DataImport,SourceFact,Anomaly,Alert,ErpOutbox,ReconciliationResult
router=APIRouter(prefix="/dashboard",tags=["dashboard"])
@router.get("/overview")
def overview(identity: Identity = Depends(require_capability("anomalies:read")),db:Session=Depends(get_db)):
    tenant_id = identity.tenant_id
    total=db.query(func.count(ReconciliationResult.id)).scalar() or 0
    mism=db.query(func.count(ReconciliationResult.id)).filter(ReconciliationResult.status=="MISMATCH").scalar() or 0
    impact=db.query(func.sum(Anomaly.financial_impact)).filter(Anomaly.tenant_id == tenant_id).scalar() or 0
    alerts_count=db.query(func.count(Alert.id)).join(Anomaly, Anomaly.id == Alert.anomaly_id).filter(Anomaly.tenant_id == tenant_id).scalar() or 0
    return {"imports":db.query(func.count(DataImport.id)).filter(DataImport.tenant_id == tenant_id).scalar() or 0,"facts":db.query(func.count(SourceFact.id)).filter(SourceFact.tenant_id == tenant_id).scalar() or 0,
      "anomalies":db.query(func.count(Anomaly.id)).filter(Anomaly.tenant_id == tenant_id).scalar() or 0,"critical":db.query(func.count(Anomaly.id)).filter(Anomaly.tenant_id == tenant_id, Anomaly.severity=="CRITICAL").scalar() or 0,
      "alerts":alerts_count,"erp_pending":db.query(func.count(ErpOutbox.id)).filter(ErpOutbox.tenant_id == tenant_id, ErpOutbox.status=="PENDING").scalar() or 0,
      "reconciliation_rate":round((1-mism/total)*100,2) if total else 100,"mismatch_rate":round(mism/total*100,2) if total else 0,
      "financial_impact":float(impact)}
