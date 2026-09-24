from app.domain.integrations.contracts import IntegrationSnapshot
from app.domain.integrations.policies import approval_required
from app.domain.integrations.service import display_label, is_terminal

def test_integrations_domain_contract_and_policy():
    snapshot = IntegrationSnapshot(identifier="integrations-001", status="OPEN", correlation_id="req-integrations")
    assert display_label(snapshot) == "integrations-001 · OPEN"
    assert is_terminal("CLOSED") is True
    assert approval_required("ERP_WRITE") is True
    assert approval_required("READ") is False
