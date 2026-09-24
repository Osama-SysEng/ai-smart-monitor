from fastapi import APIRouter
from app.api.v1 import health, imports, reconciliation, anomalies, dashboard, cases, erp, audit, security, operations
api_router=APIRouter()
for r in [health.router,imports.router,reconciliation.router,anomalies.router,dashboard.router,cases.router,erp.router,audit.router,security.router,operations.router]:
    api_router.include_router(r)

from app.api.v1.intelligence import router as intelligence_router
api_router.include_router(intelligence_router)
