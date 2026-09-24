from app.domain.reconciliation.contracts import ReconciliationSnapshot
from app.domain.reconciliation.policies import approval_required
from app.domain.reconciliation.service import display_label, is_terminal

def test_reconciliation_domain_contract_and_policy():
    snapshot = ReconciliationSnapshot(identifier="reconciliation-001", status="OPEN", correlation_id="req-reconciliation")
    assert display_label(snapshot) == "reconciliation-001 · OPEN"
    assert is_terminal("CLOSED") is True
    assert approval_required("ERP_WRITE") is True
    assert approval_required("READ") is False
