"""Read-only operator visibility endpoints."""
from fastapi import APIRouter, Depends

from app.core.identity import Identity, require_capability
from app.core.metrics import runtime_metrics

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/metrics")
def metrics(identity: Identity = Depends(require_capability("operations:read"))):
    return {"tenant_id": identity.tenant_id, "metrics": runtime_metrics.snapshot()}
