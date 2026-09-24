from app.domain.imports.contracts import ImportSnapshot
from app.domain.imports.policies import approval_required
from app.domain.imports.service import display_label, is_terminal

def test_imports_domain_contract_and_policy():
    snapshot = ImportSnapshot(identifier="imports-001", status="OPEN", correlation_id="req-imports")
    assert display_label(snapshot) == "imports-001 · OPEN"
    assert is_terminal("CLOSED") is True
    assert approval_required("ERP_WRITE") is True
    assert approval_required("READ") is False
