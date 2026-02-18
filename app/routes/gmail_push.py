# Gmail Push Webhook - Near-real-time reply processing

from __future__ import annotations
import base64
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Header, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.integrations.pubsub_auth import verify_pubsub_jwt
from app.integrations.gmail_client import gmail_service
from app.models.gmail_state import GmailState
from app.services.inbox_processor import classify_reply, upsert_optout, mark_target_replied
from app.models.inbox import InboxProcessed

router = APIRouter()

LABEL_PROCESSED_NAME = "TMD/Processed"
LABEL_OPTOUT_NAME = "TMD/OptOut"


def _b64url_decode(s: str) -> bytes:
    """Pub/Sub uses base64url encoding."""
    s = s.replace("-", "+").replace("_", "/")
    pad = "=" * (-len(s) % 4)
    return base64.b64decode(s + pad)


def _get_or_create_label_id(gmail, user_id: str, label_name: str) -> str:
    """Get or create a Gmail label."""
    labels = gmail.users().labels().list(userId=user_id).execute().get("labels", [])
    for l in labels:
        if l.get("name") == label_name:
            return l["id"]
    
    # Create label
    created = gmail.users().labels().create(
        userId=user_id,
        body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"},
    ).execute()
    return created["id"]


def _ensure_state(session: Session, email_address: str) -> GmailState:
    s = session.exec(select(GmailState).where(GmailState.email_address == email_address)).first()
    if s:
        return s
    s = GmailState(email_address=email_address, last_history_id="")
    session.add(s)
    session.commit()
    session.refresh(s)
    return s


def _history_list(gmail, user_id: str, start_history_id: str) -> List[Dict[str, Any]]:
    """Get history records since start_history_id."""
    out: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    
    while True:
        req = gmail.users().history().list(
            userId=user_id,
            startHistoryId=start_history_id,
            historyTypes=["messageAdded"],
            pageToken=page_token,
        )
        resp = req.execute()
        out.extend(resp.get("history", []) or [])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return out


def _fetch_message(gmail, user_id: str, msg_id: str) -> Dict[str, Any]:
    return gmail.users().messages().get(userId=user_id, id=msg_id, format="full").execute()


def _extract_headers(msg: Dict[str, Any]) -> Dict[str, str]:
    headers = msg.get("payload", {}).get("headers", []) or []
    return {(item.get("name") or "").lower(): item.get("value") or "" for item in headers}


def _walk_parts(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    parts = []
    stack = [payload]
    while stack:
        p = stack.pop()
        if "parts" in p:
            for child in p["parts"]:
                stack.append(child)
        else:
            parts.append(p)
    return parts


def _extract_body_text(msg: Dict[str, Any]) -> str:
    payload = msg.get("payload", {}) or {}
    parts = _walk_parts(payload)
    
    # Prefer text/plain
    for p in parts:
        if p.get("mimeType") == "text/plain":
            data = (p.get("body", {}) or {}).get("data")
            if data:
                return _b64url_decode(data).decode("utf-8", errors="replace").strip()
    
    # Fallback text/html
    for p in parts:
        if p.get("mimeType") == "text/html":
            data = (p.get("body", {}) or {}).get("data")
            if data:
                html = _b64url_decode(data).decode("utf-8", errors="replace")
                return "".join(ch if ch != "<" else " " for ch in html).strip()
    
    return ""


def _extract_email(addr: str) -> str:
    """Extract email from 'Name <email@domain.com>' format."""
    import re
    m = re.search(r"<([^>]+)>", addr or "")
    if m:
        return m.group(1).strip().lower()
    return (addr or "").strip().lower()


@router.post("/api/integrations/gmail/push")
async def gmail_push(request: Request, authorization: str = Header(default="")):
    """Handle Gmail Pub/Sub push notifications."""
    # 1) Verify JWT
    try:
        _ = verify_pubsub_jwt(authorization)
    except Exception:
        raise HTTPException(401, "invalid pubsub jwt")
    
    # 2) Parse envelope
    envelope = await request.json()
    msg = (envelope or {}).get("message") or {}
    data_b64 = msg.get("data") or ""
    
    if not data_b64:
        return {"ok": True, "ignored": "no_data"}
    
    decoded = json.loads(_b64url_decode(data_b64))
    email_address = decoded.get("emailAddress") or "me"
    history_id_new = str(decoded.get("historyId") or "")
    
    # 3) Get DB session
    session = next(get_session())
    
    # 4) Gmail client (DWD)
    gmail = gmail_service(subject_email=email_address)
    user_id = "me"
    
    # 5) Ensure labels exist
    processed_label_id = _get_or_create_label_id(gmail, user_id, LABEL_PROCESSED_NAME)
    optout_label_id = _get_or_create_label_id(gmail, user_id, LABEL_OPTOUT_NAME)
    
    # 6) Load state
    state = _ensure_state(session, email_address)
    
    if not state.last_history_id:
        # First run: set baseline only
        state.last_history_id = history_id_new
        state.updated_at = datetime.utcnow()
        session.add(state)
        session.commit()
        return {"ok": True, "baseline_set": True, "historyId": history_id_new}
    
    # 7) Pull deltas
    try:
        history = _history_list(gmail, user_id, state.last_history_id)
    except Exception:
        # Stale historyId - reset
        state.last_history_id = history_id_new
        state.updated_at = datetime.utcnow()
        session.add(state)
        session.commit()
        return {"ok": True, "history_reset": True, "historyId": history_id_new}
    
    # 8) Process new messages
    msg_ids = []
    for h in history:
        for added in (h.get("messagesAdded") or []):
            m = added.get("message") or {}
            if m.get("id"):
                msg_ids.append(m["id"])
    
    processed = 0
    optouts = 0
    
    for mid in msg_ids:
        # Idempotency
        already = session.exec(
            select(InboxProcessed).where(InboxProcessed.imap_uid == mid)
        ).first()
        if already:
            continue
        
        m = _fetch_message(gmail, user_id, mid)
        headers = _extract_headers(m)
        from_hdr = headers.get("from", "")
        subject = headers.get("subject", "")
        body = _extract_body_text(m)
        classification = classify_reply(body)
        
        # Store processed
        session.add(InboxProcessed(
            imap_uid=mid,
            from_email=from_hdr,
            subject=subject,
            classification=classification,
            meta={"body_head": (body or "")[:300]},
        ))
        session.commit()
        
        from_email = _extract_email(from_hdr)
        
        if classification == "optout":
            upsert_optout(session, email_or_domain=from_email, reason="gmail_push_optout")
            mark_target_replied(session, from_email=from_email, classification="optout", raw_subject=subject)
            gmail.users().messages().modify(
                userId=user_id,
                id=mid,
                body={"addLabelIds": [processed_label_id, optout_label_id], "removeLabelIds": []}
            ).execute()
            optouts += 1
        else:
            mark_target_replied(session, from_email=from_email, classification=classification, raw_subject=subject)
            gmail.users().messages().modify(
                userId=user_id,
                id=mid,
                body={"addLabelIds": [processed_label_id], "removeLabelIds": []}
            ).execute()
            processed += 1
    
    # 9) Update state
    state.last_history_id = history_id_new
    state.updated_at = datetime.utcnow()
    session.add(state)
    session.commit()
    
    return {"ok": True, "processed": processed, "optouts": optouts, "historyId": history_id_new}
