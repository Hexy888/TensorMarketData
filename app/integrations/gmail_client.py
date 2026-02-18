# Gmail Client - Service Account + Domain-Wide Delegation

from __future__ import annotations
import json
import os
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
GOOGLE_IMPERSONATE_USER = os.getenv("GOOGLE_IMPERSONATE_USER", "nova@tensormarketdata.com")


def _load_sa_info():
    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")
    
    # Allow either raw JSON or file path
    if GOOGLE_SERVICE_ACCOUNT_JSON.strip().startswith("{"):
        return json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
    
    with open(GOOGLE_SERVICE_ACCOUNT_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def gmail_service(subject_email: Optional[str] = None):
    info = _load_sa_info()
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=GMAIL_SCOPES
    )
    subject = subject_email or GOOGLE_IMPERSONATE_USER
    creds = creds.with_subject(subject)  # Domain-wide delegation impersonation
    return build("gmail", "v1", credentials=creds, cache_discovery=False)
