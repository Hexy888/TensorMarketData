# Gmail Watch Renewal Operations

from __future__ import annotations
import os
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.integrations.gmail_client import gmail_service
from app.models.gmail_state import GmailState

OPS_TOKEN = os.getenv("OPS_TOKEN", "")
PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "")
WATCH_LABEL_IDS = ["INBOX"]

router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


@router.post("/api/ops/gmail/watch/renew")
def renew_watch(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Renew Gmail API watch subscription. Run daily via cron."""
    if not PUBSUB_TOPIC:
        raise HTTPException(500, "PUBSUB_TOPIC not set")
    
    gmail = gmail_service()
    user_id = "me"
    
    req = {
        "topicName": PUBSUB_TOPIC,
        "labelIds": WATCH_LABEL_IDS,
        "labelFilterBehavior": "INCLUDE",
    }
    
    resp = gmail.users().watch(userId=user_id, body=req).execute()
    
    history_id = str(resp.get("historyId") or "")
    expiration = int(resp.get("expiration") or 0)
    
    email_address = os.getenv("GOOGLE_IMPERSONATE_USER", "nova@tensormarketdata.com")
    
    state = session.exec(select(GmailState).where(GmailState.email_address == email_address)).first()
    
    if not state:
        state = GmailState(
            email_address=email_address,
            last_history_id=history_id,
            watch_expiration_ms=expiration
        )
    else:
        if not state.last_history_id and history_id:
            state.last_history_id = history_id
        state.watch_expiration_ms = expiration
    
    state.updated_at = datetime.utcnow()
    session.add(state)
    session.commit()
    
    return {"ok": True, "historyId": history_id, "expiration": expiration}
