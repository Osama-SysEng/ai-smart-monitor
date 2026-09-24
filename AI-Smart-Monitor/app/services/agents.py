from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Anomaly, InvestigationCase, AuditLog
from app.services.ai import get_provider

@dataclass
class AgentDecision:
    agent:str; action:str; confidence:float; rationale:str; requires_approval:bool

class MonitoringAgent:
    name="monitoring_agent"
    def investigate(self, db:Session, anomaly:Anomaly):
        history=db.query(Anomaly).filter(Anomaly.item_code==anomaly.item_code).limit(50).all()
        repeat=len(history)>1
        evidence={**(anomaly.facts or {}),"facts":anomaly.evidence or [],
                  "historical_repeat":repeat,"financial_impact":anomaly.financial_impact}
        analysis=get_provider().analyze(evidence)
        confidence=float(analysis.get("confidence",0))
        risk=anomaly.severity in {"HIGH","CRITICAL"} or anomaly.financial_impact>=10000
        decision=AgentDecision(self.name,"ESCALATE" if risk else "INVESTIGATE",confidence,
                               analysis.get("summary",""),risk)
        anomaly.facts={**(anomaly.facts or {}),"ai_analysis":analysis,
                       "agent_decision":decision.__dict__}
        db.add(AuditLog(actor="agent:monitoring",action="AGENT_DECISION",entity_type="Anomaly",
                        entity_id=str(anomaly.id),new_value=decision.__dict__,reason=decision.rationale))
        db.commit()
        return decision

class RootCauseAgent:
    name="root_cause_agent"
    def analyze(self,db,anomaly):
        analysis=(anomaly.facts or {}).get("ai_analysis",{})
        causes=analysis.get("possible_causes",[])
        top=max(causes,key=lambda x:float(x.get("confidence",0)),default=None)
        return top or {"cause":"Insufficient evidence","classification":"UNKNOWN","confidence":0.0}

class ForecastAgent:
    name="forecast_agent"
    def forecast(self,db,item_code):
        rows=db.query(Anomaly).filter(Anomaly.item_code==item_code).order_by(Anomaly.created_at.desc()).limit(20).all()
        return {"item_code":item_code,"observations":len(rows),
                "repeat_risk":"HIGH" if len(rows)>=3 else "LOW" if len(rows)==0 else "MEDIUM"}

class AgentOrchestrator:
    def __init__(self): self.monitoring=MonitoringAgent(); self.root=RootCauseAgent(); self.forecast=ForecastAgent()
    def run(self,db,anomaly):
        decision=self.monitoring.investigate(db,anomaly)
        root=self.root.analyze(db,anomaly)
        anomaly.facts={**(anomaly.facts or {}),"root_cause":root}
        db.add(AuditLog(actor="agent:root_cause",action="ROOT_CAUSE_ANALYZED",entity_type="Anomaly",
                        entity_id=str(anomaly.id),new_value=root))
        db.commit()
        return {"decision":decision.__dict__,"root_cause":root}
