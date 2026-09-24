from app.domain.cases.contracts import CaseSnapshot
from app.domain.cases.policies import approval_required
from app.domain.cases.service import display_label, is_terminal

def test_cases_domain_contract_and_policy():
    snapshot = CaseSnapshot(identifier="cases-001", status="OPEN", correlation_id="req-cases")
    assert display_label(snapshot) == "cases-001 · OPEN"
    assert is_terminal("CLOSED") is True
    assert approval_required("ERP_WRITE") is True
    assert approval_required("READ") is False
