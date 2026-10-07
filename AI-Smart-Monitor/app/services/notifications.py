from datetime import datetime, timezone
import httpx
from app.core.config import settings
def telegram(title,message):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return {"sent":False,"reason":"telegram_not_configured"}
    text = f"{title}\n\n{message}"
    if len(text) > 4000:
        text = text[:3997] + "..."
    url=f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        r=httpx.post(url,json={"chat_id":settings.telegram_chat_id,"text":text},timeout=10)
        if r.is_success:
            return {"sent":True,"status":r.status_code}
        return {"sent":False,"status":r.status_code,"error_category":"REMOTE_CLIENT" if r.status_code < 500 else "REMOTE_SERVER","error":r.text[:300]}
    except httpx.TimeoutException:return {"sent":False,"error_category":"TIMEOUT","error":"telegram request timed out"}
    except Exception as e:return {"sent":False,"error_category":"TRANSPORT","error":str(e)[:300]}
