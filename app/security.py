import hashlib
import hmac
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer
from app.config import settings

# Session cookie signing
session_serializer = URLSafeSerializer(settings.secret_key, salt="tmd-session")

# Magic link signing (time limited)
magic_serializer = URLSafeTimedSerializer(settings.secret_key, salt="tmd-magic")

def hash_password(password: str) -> str:
    return hashlib.sha256((settings.secret_key + password).encode("utf-8")).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    test = hash_password(password)
    return hmac.compare_digest(test, password_hash)

def sign_session(data: dict) -> str:
    return session_serializer.dumps(data)

def unsign_session(token: str):
    try:
        return session_serializer.loads(token)
    except Exception:
        return None

def make_magic_token(email: str) -> str:
    return magic_serializer.dumps({"email": email})

def verify_magic_token(token: str, max_age_seconds: int = 1800) -> dict | None:
    try:
        return magic_serializer.loads(token, max_age=max_age_seconds)
    except Exception:
        return None
