import time
import base64
import json
import hmac
import hashlib
import os

SECRET = os.getenv("APP_SECRET", "dev-secret-change-me").encode()

def sign(data: dict, ttl_seconds: int = 1800) -> str:
    payload = dict(data)
    payload["exp"] = int(time.time()) + ttl_seconds
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    mac = hmac.new(SECRET, raw, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(raw + b"." + mac).decode()
    return token

def verify(token: str) -> dict | None:
    try:
        blob = base64.urlsafe_b64decode(token.encode())
        raw, mac = blob.rsplit(b".", 1)
        expect = hmac.new(SECRET, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expect):
            return None
        data = json.loads(raw.decode())
        if int(time.time()) > int(data.get("exp", 0)):
            return None
        return data
    except Exception:
        return None
