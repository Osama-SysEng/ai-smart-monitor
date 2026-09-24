from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import AuditLog
from app.core.identity import Identity, require_capability
router=APIRouter(prefix="/audit",tags=["audit"])
@router.get("")
def audit(limit: int = Query(default=100, ge=1, le=500), identity: Identity = Depends(require_capability("audit:read")), db:Session=Depends(get_db)):
    return db.query(AuditLog).filter(AuditLog.tenant_id == identity.tenant_id).order_by(AuditLog.id.desc()).limit(limit).all()
