import hashlib, json
from app.models import AuditLog
def append_hash(db,event:AuditLog):
    prev=db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash=(prev.new_value or {}).get("_audit_hash","") if prev else ""
    body={"actor":event.actor,"action":event.action,"entity_id":event.entity_id,
          "old":event.old_value,"new":event.new_value,"previous_hash":previous_hash}
    digest=hashlib.sha256(json.dumps(body,sort_keys=True,default=str).encode()).hexdigest()
    event.new_value={**(event.new_value or {}),"_audit_hash":digest}
    return event
