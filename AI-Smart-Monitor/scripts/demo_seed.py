import asyncio,os
from app.db.session import SessionLocal,init_db
from app.models import SourceFact
from app.services.reconciliation import reconcile
def seed():
 init_db();db=SessionLocal()
 for source,rows in {
 "warehouse":[("DIS-10482","ITEM-A",7,150),("DIS-100","ITEM-A",100,10),("DIS-200","ITEM-B",40,25)],
 "branch":[("DIS-10482","ITEM-A",6,150),("DIS-100","ITEM-A",97,10),("DIS-200","ITEM-B",40,25)],
 "cost":[("DIS-10482","ITEM-A",5,150),("DIS-100","ITEM-A",95,10),("DIS-200","ITEM-B",40,25)]
 }.items():
  for tx,item,q,c in rows:
   import hashlib
   rh=hashlib.sha256(f"{source}|{tx}|{item}".encode()).hexdigest()
   if not db.query(SourceFact).filter_by(record_hash=rh).first():
    db.add(SourceFact(transaction_id=tx,item_code=item,source_id=source,quantity=q,cost=c,record_hash=rh,import_id=0,raw_payload={}))
 db.commit(); print(reconcile(db).summary)
if __name__=="__main__":seed()
