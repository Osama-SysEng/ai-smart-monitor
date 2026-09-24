from datetime import datetime, timezone
import httpx
from app.core.config import settings
def telegram(title,message):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return {"sent":False,"reason":"telegram_not_configured"}
    url=f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        r=httpx.post(url,json={"chat_id":settings.telegram_chat_id,"text":f"{title}\n\n{message}"},timeout=10)
        return {"sent":r.is_success,"status":r.status_code}
    except Exception as e:return {"sent":False,"error":str(e)}
