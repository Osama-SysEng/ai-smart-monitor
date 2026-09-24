from app.domain.alerts.contracts import AlertSnapshot
from app.domain.alerts.policies import approval_required
from app.domain.alerts.service import display_label, is_terminal

def test_alerts_domain_contract_and_policy():
    snapshot = AlertSnapshot(identifier="alerts-001", status="OPEN", correlation_id="req-alerts")
    assert display_label(snapshot) == "alerts-001 · OPEN"
    assert is_terminal("CLOSED") is True
    assert approval_required("ERP_WRITE") is True
    assert approval_required("READ") is False
