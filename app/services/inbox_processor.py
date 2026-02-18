# Inbox Processor - IMAP-based reply parsing

from __future__ import annotations
import os
import re
import ssl
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from sqlmodel import Session, select

from app.models.outbound import OutboundTarget, OutboundOptOut, OutboundEvent
from app.models.inbox import InboxProcessed

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASS = os.getenv("IMAP_PASS", "")
IMAP_FOLDER = os.getenv("IMAP_FOLDER", "INBOX")
LABEL_PROCESSED = os.getenv("IMAP_LABEL_PROCESSED", "TMD/Processed")
LABEL_OPTOUT = os.getenv("IMAP_LABEL_OPTOUT", "TMD/OptOut")
LOOKBACK_DAYS = int(os.getenv("INBOX_LOOKBACK_DAYS", "14"))


# --- Classification patterns ---
OPTOUT_PAT = re.compile(r"\b(opt\s*out|unsubscribe|remove me|do not contact)\b", re.I)
YES_PAT = re.compile(r"^\s*(yes|yeah|yep|sure|interested|send it|sounds good)\s*[\.\!]*\s*$", re.I)
LATER_PAT = re.compile(r"\b(not now|later|next month|check back|in a few weeks)\b", re.I)
QUESTION_PAT = re.compile(r"\?$")


def _decode_mime_words(s: str) -> str:
    parts = decode_header(s)
    out = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="replace")
        else:
            out += text
    return out


def _extract_plain_text(msg: email.message.Message) -> str:
    """Prefer text/plain. Fallback to stripping minimal HTML."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "").lower()
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True) or b""
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace").strip()
        
        # Fallback: first text/html
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                html = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                return re.sub(r"<[^>]+>", " ", html).replace("&nbsp;", " ").strip()
    else:
        payload = msg.get_payload(decode=True) or b""
        text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
        if msg.get_content_type() == "text/html":
            text = re.sub(r"<[^>]+>", " ", text).replace("&nbsp;", " ")
        return text.strip()
    return ""


def classify_reply(body: str) -> str:
    b = (body or "").strip()
    if not b:
        return "unknown"
    
    if OPTOUT_PAT.search(b):
        return "optout"
    
    first_line = b.splitlines()[0] if b else ""
    if YES_PAT.match(first_line):
        return "yes"
    
    if LATER_PAT.search(b):
        return "later"
    
    # If contains questions, treat as question
    if "?" in b or QUESTION_PAT.search(first_line):
        return "question"
    
    return "unknown"


def _email_addr_from_from_header(from_header: str) -> str:
    """Extract email from 'Name <email@domain.com>' format."""
    m = re.search(r"<([^>]+)>", from_header or "")
    if m:
        return m.group(1).strip().lower()
    return (from_header or "").strip().lower()


def _domain_from_email(addr: str) -> Optional[str]:
    if "@" not in addr:
        return None
    return addr.split("@", 1)[1].strip().lower()


class GmailIMAP:
    def __init__(self):
        if not (IMAP_USER and IMAP_PASS):
            raise RuntimeError("IMAP_USER/IMAP_PASS not set")
        ctx = ssl.create_default_context()
        self.client = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ctx)
    
    def login(self):
        self.client.login(IMAP_USER, IMAP_PASS)
    
    def select_inbox(self):
        self.client.select(IMAP_FOLDER)
    
    def logout(self):
        try:
            self.client.logout()
        except Exception:
            pass
    
    def search_since(self, since_date: datetime) -> List[bytes]:
        """Return message sequence ids."""
        since_str = since_date.strftime("%d-%b-%Y")
        status, data = self.client.search(None, f'(SINCE "{since_str}")')
        if status != "OK":
            return []
        return data[0].split()
    
    def fetch_uid_and_rfc822(self, msg_id: bytes) -> Tuple[str, bytes]:
        status, data = self.client.fetch(msg_id, "(UID RFC822)")
        if status != "OK" or not data or not data[0]:
            raise RuntimeError("fetch failed")
        
        meta = data[0][0].decode("utf-8", errors="ignore")
        uid_match = re.search(r"UID\s+(\d+)", meta)
        uid = uid_match.group(1) if uid_match else ""
        raw = data[0][1]
        return uid, raw
    
    def add_gmail_label(self, msg_id: bytes, label: str):
        """Gmail IMAP extension: X-GM-LABELS"""
        self.client.store(msg_id, "+X-GM-LABELS", f'("{label}")')


def upsert_optout(session: Session, *, email_or_domain: str, reason: str = "inbox_optout") -> None:
    key = (email_or_domain or "").strip().lower()
    if not key:
        return
    existing = session.exec(select(OutboundOptOut).where(OutboundOptOut.email_or_domain == key)).first()
    if existing:
        return
    session.add(OutboundOptOut(email_or_domain=key, reason=reason))
    session.commit()


def mark_target_replied(session: Session, *, from_email: str, classification: str, raw_subject: str) -> Optional[int]:
    """Link reply to outbound target."""
    fe = (from_email or "").strip().lower()
    if not fe:
        return None
    
    t = session.exec(select(OutboundTarget).where(OutboundTarget.contact_email == fe)).first()
    if not t or t.id is None:
        return None
    
    # Update status
    if classification == "yes":
        t.status = "replied"
    elif classification == "optout":
        t.status = "opted_out"
    else:
        t.status = "replied"
    
    t.updated_at = datetime.utcnow()
    session.add(t)
    
    # Event log
    session.add(
        OutboundEvent(
            target_id=t.id,
            event_type="reply",
            meta={"classification": classification, "subject": raw_subject[:200]},
        )
    )
    session.commit()
    return t.id


def process_inbox(session: Session) -> Dict[str, Any]:
    """Poll inbox, classify replies, update DB, label emails."""
    since = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    
    imap = GmailIMAP()
    imap.login()
    imap.select_inbox()
    
    stats = {
        "ok": True,
        "seen": 0,
        "processed": 0,
        "optouts": 0,
        "yes": 0,
        "questions": 0,
        "later": 0,
        "unknown": 0
    }
    
    try:
        msg_ids = imap.search_since(since)
        stats["seen"] = len(msg_ids)
        
        for msg_id in msg_ids:
            try:
                uid, raw = imap.fetch_uid_and_rfc822(msg_id)
                if not uid:
                    continue
                
                # Check idempotency
                already = session.exec(
                    select(InboxProcessed).where(InboxProcessed.imap_uid == uid)
                ).first()
                if already:
                    continue
                
                msg = email.message_from_bytes(raw)
                subject = _decode_mime_words(msg.get("Subject", "") or "")
                from_hdr = msg.get("From", "") or ""
                from_email = _email_addr_from_from_header(from_hdr)
                body = _extract_plain_text(msg)
                classification = classify_reply(body)
                
                # Persist processed marker FIRST
                session.add(
                    InboxProcessed(
                        imap_uid=uid,
                        from_email=from_email,
                        subject=subject,
                        classification=classification,
                        meta={"from_header": from_hdr[:200], "body_head": body[:300]},
                    )
                )
                session.commit()
                
                # Apply business logic
                if classification == "optout":
                    upsert_optout(session, email_or_domain=from_email, reason="inbox_optout")
                    dom = _domain_from_email(from_email)
                    if dom:
                        upsert_optout(session, email_or_domain=dom, reason="inbox_optout_domain")
                    mark_target_replied(session, from_email=from_email, classification="optout", raw_subject=subject)
                    imap.add_gmail_label(msg_id, LABEL_OPTOUT)
                    stats["optouts"] += 1
                else:
                    mark_target_replied(session, from_email=from_email, classification=classification, raw_subject=subject)
                    imap.add_gmail_label(msg_id, LABEL_PROCESSED)
                
                # Counters
                if classification == "yes":
                    stats["yes"] += 1
                elif classification == "question":
                    stats["questions"] += 1
                elif classification == "later":
                    stats["later"] += 1
                else:
                    stats["unknown"] += 1
                
                stats["processed"] += 1
                
            except Exception:
                continue
    finally:
        imap.logout()
    
    return stats
