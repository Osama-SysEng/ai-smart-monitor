from datetime import datetime, timezone
import httpx
from app.core.config import settings

class ERPAdapter:
    def push(self,event_type,payload,idempotency_key):
        if not settings.erp_base_url:
            return {"status":"NOT_CONFIGURED","idempotency_key":idempotency_key,"retryable":False,"error_category":"CONFIGURATION"}
        try:
            r=httpx.post(f"{settings.erp_base_url.rstrip('/')}/events",
                         headers={"Authorization":f"Bearer {settings.erp_api_key}","Idempotency-Key":idempotency_key},
                         json={"event_type":event_type,"payload":payload},timeout=settings.erp_timeout)
            if r.is_success:
                return {"status":"SENT","http_status":r.status_code,"retryable":False,"at":datetime.now(timezone.utc).isoformat()}
            retryable = r.status_code >= 500 or r.status_code in {408, 429}
            return {"status":"FAILED","http_status":r.status_code,"retryable":retryable,"error_category":"REMOTE_SERVER" if retryable else "REMOTE_CLIENT","body":r.text[:500],"at":datetime.now(timezone.utc).isoformat()}
        except httpx.TimeoutException:
            return {"status":"FAILED","retryable":True,"error_category":"TIMEOUT","error":"ERP request timed out"}
        except httpx.HTTPError as e:
            return {"status":"FAILED","retryable":True,"error_category":"TRANSPORT","error":str(e)[:300]}
