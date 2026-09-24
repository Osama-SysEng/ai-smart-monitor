from app.domain.anomalies.contracts import AnomalySnapshot
from app.domain.anomalies.policies import approval_required
from app.domain.anomalies.service import display_label, is_terminal

def test_anomalies_domain_contract_and_policy():
    snapshot = AnomalySnapshot(identifier="anomalies-001", status="OPEN", correlation_id="req-anomalies")
    assert display_label(snapshot) == "anomalies-001 · OPEN"
    assert is_terminal("CLOSED") is True
    assert approval_required("ERP_WRITE") is True
    assert approval_required("READ") is False
