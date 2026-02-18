# Pub/Sub Push JWT Verification

from __future__ import annotations
import os
from typing import Dict, Any
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

PUBSUB_AUDIENCE = os.getenv("PUBSUB_AUDIENCE", "https://tensormarketdata.com/api/integrations/gmail/push")


def verify_pubsub_jwt(auth_header: str) -> Dict[str, Any]:
    """
    Verify Pub/Sub push JWT.
    Expected: Authorization: Bearer <JWT>
    """
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise ValueError("missing bearer token")
    
    token = auth_header.split(" ", 1)[1].strip()
    req = google_requests.Request()
    claims = id_token.verify_oauth2_token(token, req, audience=PUBSUB_AUDIENCE)
    return claims
