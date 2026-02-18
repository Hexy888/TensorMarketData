# Inbox Operations Routes

import os
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.services.inbox_processor import process_inbox

OPS_TOKEN = os.getenv("OPS_TOKEN", "")

router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


@router.post("/api/ops/inbox/poll")
def inbox_poll(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """
    Poll inbox for new replies, classify, update DB, and label emails.
    Run every 10 minutes via cron.
    """
    return process_inbox(session)
