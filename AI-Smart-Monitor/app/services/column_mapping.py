import re
from rapidfuzz import process, fuzz

ALIASES = {
 "transaction_id":["transaction_id","transaction id","tx_id","transaction","reference","dispatch_id"],
 "item_code":["item_code","item code","sku","product_code","product code","item"],
 "quantity":["quantity","qty","units","count","received_qty","dispatched_qty"],
 "cost":["cost","unit_cost","unit cost","amount","value"],
 "business_date":["date","business_date","transaction_date","created_at"],
 "branch_code":["branch","branch_code","branch id"],
 "warehouse_code":["warehouse","warehouse_code","warehouse id"],
 "supplier_code":["supplier","supplier_code","vendor","vendor_code"],
}

def norm(s): return re.sub(r"[^a-z0-9]+","_",str(s).strip().lower()).strip("_")

def suggest_mapping(columns):
    result={}
    for c in columns:
        n=norm(c)
        exact=next((k for k,v in ALIASES.items() if n in [norm(x) for x in v]),None)
        if exact: result[c]={"field":exact,"score":100,"method":"exact_or_alias"}; continue
        choices=[(alias,field) for field,aliases in ALIASES.items() for alias in aliases]
        match=process.extractOne(n,[norm(a) for a,_ in choices],scorer=fuzz.WRatio)
        if match and match[1]>=75:
            field=choices[match[2]][1]
            result[c]={"field":field,"score":round(match[1]),"method":"fuzzy"}
        else: result[c]={"field":None,"score":0,"method":"unknown"}
    return result
