from app.services.severity import severity
from app.services.column_mapping import suggest_mapping
def test_severity(): assert severity(0,0)=="INFO"; assert severity(30,5000)=="CRITICAL"
def test_mapping(): assert suggest_mapping(["SKU","Qty"])["SKU"]["field"]=="item_code"; assert suggest_mapping(["Qty"])["Qty"]["field"]=="quantity"
