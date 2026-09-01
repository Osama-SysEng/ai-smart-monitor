from app.services.policy import action_policy
class A:
    def __init__(self,severity,impact=0): self.severity=severity; self.financial_impact=impact
def test_high_risk_requires_approval():
    assert action_policy(A("CRITICAL"),"ERP_WRITE")=="APPROVAL_REQUIRED"
    assert action_policy(A("LOW"),"ERP_WRITE")=="APPROVAL_REQUIRED"
def test_low_risk_analysis_allowed():
    assert action_policy(A("LOW"),"NOTIFY")=="AUTONOMOUS_ALLOWED"
