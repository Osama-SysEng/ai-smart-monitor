import hashlib, hmac, time
from fastapi import Header, HTTPException
from app.core.config import settings

def verify_api_key(x_api_key: str | None = Header(default=None)):
    if settings.environment == "development" and not settings.require_api_key:
        return {"role":"admin","tenant_id":"default","actor":"dev"}
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"role":"admin","tenant_id":"default","actor":"api_key"}

def require_role(role: str):
    def dep(ctx=verify_api_key):
        if ctx["role"] != role and ctx["role"] != "admin":
            raise HTTPException(status_code=403, detail="Insufficient role")
        return ctx
    return dep
