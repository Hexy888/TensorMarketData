# Google OAuth for GBP

from __future__ import annotations
import os
import urllib.parse
from typing import Dict, Any
import requests
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

BASE_URL = os.getenv("BASE_URL", "https://tensormarketdata.com").rstrip("/")
CLIENT_ID = os.getenv("GBP_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GBP_OAUTH_CLIENT_SECRET", "")
STATE_SECRET = os.getenv("OAUTH_STATE_SECRET", "")

SCOPE = "https://www.googleapis.com/auth/business.manage"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_PATH = "/app/oauth/google/callback"
REDIRECT_URI = f"{BASE_URL}{REDIRECT_PATH}"

_serializer = URLSafeTimedSerializer(STATE_SECRET, salt="gbp-oauth")


def require_oauth_env():
    if not CLIENT_ID or not CLIENT_SECRET or not STATE_SECRET:
        raise RuntimeError("Missing GBP_OAUTH_CLIENT_ID/GBP_OAUTH_CLIENT_SECRET/OAUTH_STATE_SECRET")


def make_state(payload: Dict[str, Any]) -> str:
    require_oauth_env()
    return _serializer.dumps(payload)


def read_state(state: str, max_age_seconds: int = 900) -> Dict[str, Any]:
    require_oauth_env()
    try:
        return _serializer.loads(state, max_age=max_age_seconds)
    except SignatureExpired as e:
        raise RuntimeError("oauth state expired") from e
    except BadSignature as e:
        raise RuntimeError("bad oauth state") from e


def build_auth_redirect(client_id: int) -> str:
    """Build OAuth consent URL with offline access."""
    state = make_state({"client_id": client_id})
    q = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(q)}"


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange authorization code for tokens."""
    require_oauth_env()
    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    r = requests.post(TOKEN_URL, data=data, timeout=20)
    r.raise_for_status()
    return r.json()


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """Refresh access token."""
    require_oauth_env()
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    r = requests.post(TOKEN_URL, data=data, timeout=20)
    r.raise_for_status()
    return r.json()
