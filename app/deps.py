import os
from fastapi import Request, HTTPException, Header

# Load secret once
SECRET = (os.getenv("APP_SECRET") or os.getenv("SECRET_KEY") or "dev-secret-change-me").encode()
COOKIE_NAME = "tmd_session"
OPS_TOKEN = os.getenv("OPS_TOKEN", "")

def verify_session(token: str) -> dict | None:
    import json, base64, hmac, hashlib
    try:
        blob = base64.urlsafe_b64decode(token.encode())
        raw, mac = blob.rsplit(b".", 1)
        expect = hmac.new(SECRET, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expect):
            return None
        data = json.loads(raw.decode())
        import time
        if int(time.time()) > int(data.get("exp", 0)):
            return None
        return data
    except Exception:
        return None

def require_user(request: Request) -> dict:
    token = request.cookies.get(COOKIE_NAME, "")
    data = verify_session(token)
    if not data:
        raise HTTPException(status_code=401, detail="unauthorized")
    return data

def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(status_code=500, detail="OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(status_code=401, detail="bad ops token")
    return True
