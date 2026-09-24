from fastapi import APIRouter, UploadFile, File, Form, Depends, Request, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import DataImport
from app.core.identity import Identity, require_capability
from app.services.ingestion import ingest
router=APIRouter(prefix="/imports",tags=["imports"])
@router.post("")
async def upload(request: Request, file:UploadFile=File(...),source_id:str=Form(...),identity: Identity = Depends(require_capability("imports:write")),db:Session=Depends(get_db)):
    return await ingest(file,source_id,db,request.headers.get("X-Request-Id"), tenant_id=identity.tenant_id, actor=identity.actor)
@router.get("")
def list_imports(limit:int=Query(default=50,ge=1,le=200),source_id:str|None=None,identity: Identity = Depends(require_capability("imports:read")),db:Session=Depends(get_db)):
    query=db.query(DataImport).filter(DataImport.tenant_id == identity.tenant_id)
    if source_id: query=query.filter(DataImport.source_id==source_id.strip().lower())
    return query.order_by(DataImport.id.desc()).limit(limit).all()
