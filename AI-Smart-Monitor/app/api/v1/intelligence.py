from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Anomaly
from app.services.agents import AgentOrchestrator
from app.services.policy import action_policy
router=APIRouter(prefix="/intelligence",tags=["intelligence"])
@router.post("/anomalies/{anomaly_id}/investigate")
def investigate(anomaly_id:int,db:Session=Depends(get_db)):
    a=db.get(Anomaly,anomaly_id)
    if not a: raise HTTPException(404,"Anomaly not found")
    return AgentOrchestrator().run(db,a)
@router.get("/anomalies/{anomaly_id}/policy/{action}")
def policy(anomaly_id:int,action:str,db:Session=Depends(get_db)):
    a=db.get(Anomaly,anomaly_id)
    if not a: raise HTTPException(404,"Anomaly not found")
    return {"decision":action_policy(a,action.upper()),"severity":a.severity}
