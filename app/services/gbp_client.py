import os
import time
import json
import base64
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet, InvalidToken

SCOPE_DEFAULT = "https://www.googleapis.com/auth/business.manage"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Business Profile APIs
ACCOUNTS_BASE = "https://mybusinessaccountmanagement.googleapis.com/v1"
INFO_BASE = "https://mybusinessbusinessinformation.googleapis.com/v1"
REVIEWS_BASE_V4 = "https://mybusiness.googleapis.com/v4"

def _get_fernet() -> Optional[Fernet]:
    key = os.getenv("TMD_TOKEN_KEY", "").strip()
    if not key:
        return None
    try:
        return Fernet(key.encode())
    except Exception:
        return None

def encrypt_refresh_token(token: str) -> str:
    f = _get_fernet()
    if not f:
        return token  # fallback plaintext
    return f.encrypt(token.encode()).decode()

def decrypt_refresh_token(token_enc: str) -> str:
    f = _get_fernet()
    if not f:
        return token_enc
    try:
        return f.decrypt(token_enc.encode()).decode()
    except InvalidToken:
        return ""

def build_auth_url(state: str) -> str:
    from urllib.parse import urlencode
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")
    scopes = os.getenv("GOOGLE_OAUTH_SCOPES", SCOPE_DEFAULT)
    
    if not client_id or not redirect_uri:
        raise RuntimeError("Missing GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_REDIRECT_URI")
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scopes,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return AUTH_URL + "?" + urlencode(params)

def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    redirect_uri = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")
    
    r = requests.post(
        TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    
    r = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def api_get(url: str, access_token: str) -> Dict[str, Any]:
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    r.raise_for_status()
    return r.json()

def api_post(url: str, access_token: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(url, headers={"Authorization": f"Bearer {access_token}"}, json=json_body, timeout=30)
    r.raise_for_status()
    return r.json()

def list_accounts(access_token: str) -> List[Dict[str, Any]]:
    data = api_get(f"{ACCOUNTS_BASE}/accounts", access_token)
    return data.get("accounts", [])

def list_locations(access_token: str, account_name: str) -> List[Dict[str, Any]]:
    data = api_get(f"{INFO_BASE}/{account_name}/locations?readMask=name,title,storefrontAddress", access_token)
    return data.get("locations", [])

def list_reviews_v4(access_token: str, location_name: str, page_size: int = 50) -> List[Dict[str, Any]]:
    url = f"{REVIEWS_BASE_V4}/{location_name}/reviews?pageSize={max(1,min(page_size,200))}"
    data = api_get(url, access_token)
    return data.get("reviews", [])

def list_reviews_v4_page(access_token: str, location_name: str, page_size: int = 50, page_token: str | None = None) -> dict:
    url = f"{REVIEWS_BASE_V4}/{location_name}/reviews?pageSize={max(1,min(page_size,200))}"
    if page_token:
        url += f"&pageToken={page_token}"
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=30)
    r.raise_for_status()
    return r.json()

def list_reviews_v4_all(access_token: str, location_name: str, page_size: int = 50, max_pages: int = 6) -> list:
    """Returns combined list of reviews across pages (capped)."""
    reviews = []
    token = None
    for _ in range(max(1, max_pages)):
        data = list_reviews_v4_page(access_token, location_name, page_size=page_size, page_token=token)
        reviews.extend(data.get("reviews", []))
        token = data.get("nextPageToken")
        if not token:
            break
    return reviews

def reply_to_review_v4(access_token: str, review_name: str, comment: str) -> Dict[str, Any]:
    # Placeholder for reply posting
    url = f"{REVIEWS_BASE_V4}/{review_name}/reply"
    return api_post(url, access_token, {"comment": comment})

def update_reply_v4(access_token: str, review_name: str, comment: str) -> dict:
    """
    Implements accounts.locations.reviews.updateReply:
    PUT /v4/{name=accounts/*/locations/*/reviews/*}/reply
    Body: { "comment": "..." }
    """
    url = f"{REVIEWS_BASE_V4}/{review_name}/reply"
    r = requests.put(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        json={"comment": comment},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
