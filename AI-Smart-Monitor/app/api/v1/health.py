from fastapi import APIRouter, HTTPException, status
from app.db.session import engine
router=APIRouter(tags=["health"])
@router.get("/health")
def health(): return {"status":"ok"}
@router.get("/ready")
def ready():
    try:
        with engine.connect() as c: c.exec_driver_sql("SELECT 1")
        return {"status":"ready","database":"ok"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"status":"not_ready","database":"error"}) from e
