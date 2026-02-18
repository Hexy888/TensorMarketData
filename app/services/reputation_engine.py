# Reputation Engine - Core business logic with retries + throttling + alerts

from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select

from app.models.reputation import Client, ClientLocation, Review, ReplyDraft, WeeklyReport
from app.models.alerts import Alert
from app.services.retry import retry_call
from app.integrations.gbp_client import (
    GBPClient, GBPAPIError, is_retryable_gbp_error, is_quota_error, is_auth_error, is_verified_location_error
)

# Config
GBP_MAX_RETRIES = int(os.getenv("GBP_MAX_RETRIES", "5"))
GBP_BACKOFF_BASE_SEC = float(os.getenv("GBP_BACKOFF_BASE_SEC", "1.5"))
GBP_BACKOFF_MAX_SEC = float(os.getenv("GBP_BACKOFF_MAX_SEC", "30"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "4"))
OPENAI_BACKOFF_BASE_SEC = float(os.getenv("OPENAI_BACKOFF_BASE_SEC", "1.0"))
OPENAI_BACKOFF_MAX_SEC = float(os.getenv("OPENAI_BACKOFF_MAX_SEC", "20"))
THROTTLE_GLOBAL_PER_RUN = int(os.getenv("THROTTLE_GLOBAL_PER_RUN", "50"))
THROTTLE_PER_CLIENT_PER_RUN = int(os.getenv("THROTTLE_PER_CLIENT_PER_RUN", "15"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_REPLY_CHARS = int(os.getenv("GBP_MAX_REPLY_CHARS", "600"))


def _safe_trim(s: str, n: int) -> str:
    s = (s or "").strip()
    return s[:n].strip()


def _create_or_bump_alert(
    session: Session,
    *,
    severity: str,
    kind: str,
    message: str,
    client_id: int | None = None,
    location_id: int | None = None,
    meta: Dict[str, Any] | None = None,
):
    """Idempotent alert creation."""
    meta = meta or {}
    
    existing = session.exec(
        select(Alert).where(
            Alert.status == "open",
            Alert.kind == kind,
            Alert.client_id == client_id,
            Alert.location_id == location_id,
            Alert.message == message
        )
    ).first()
    
    if existing:
        existing.updated_at = datetime.utcnow()
        m = existing.meta or {}
        m["count"] = int(m.get("count", 1)) + 1
        existing.meta = {**m, **meta}
        session.add(existing)
    else:
        session.add(Alert(
            severity=severity,
            kind=kind,
            message=message,
            client_id=client_id,
            location_id=location_id,
            meta={**meta, "count": 1}
        ))
    session.commit()


def draft_reply_llm(client_name: str, rating: int, comment: str) -> str:
    """Generate professional review reply using LLM with retry."""
    from openai import OpenAI
    
    prompt = f"""
You are writing a public Google review reply for a local service business.
Constraints:
- Max {MAX_REPLY_CHARS} characters.
- Sound professional, calm, helpful.
- Do NOT offer discounts, gifts, or incentives.
- Do NOT mention internal processes.
- If rating is 1-3, acknowledge issue, invite offline resolution, avoid blame.
- If rating is 4-5, thank them and reinforce service.

Business: {client_name}
Rating: {rating}/5
Review text: {comment}

Return ONLY the reply text.
""".strip()
    
    def _call():
        client = OpenAI()
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        return resp.choices[0].message.content or ""
    
    def _should_retry(e: Exception) -> bool:
        s = str(e).lower()
        return ("429" in s) or ("timeout" in s) or ("temporarily" in s) or ("503" in s) or ("502" in s)
    
    txt = retry_call(
        _call,
        max_retries=OPENAI_MAX_RETRIES,
        backoff_base=OPENAI_BACKOFF_BASE_SEC,
        backoff_cap=OPENAI_BACKOFF_MAX_SEC,
        should_retry=_should_retry,
    )
    return _safe_trim(txt, MAX_REPLY_CHARS)


class ReputationEngine:
    def __init__(self, session: Session):
        self.session = session
    
    # -------- Ingest --------
    def ingest_reviews(self) -> Dict[str, Any]:
        created = 0
        updated = 0
        errors = 0
        global_calls = 0
        
        clients = self.session.exec(
            select(Client).where(Client.status == "active")
        ).all()
        
        for c in clients:
            if global_calls >= THROTTLE_GLOBAL_PER_RUN:
                break
            if not c.gbp_refresh_token:
                continue
            
            per_client_calls = 0
            gbp = GBPClient(refresh_token=c.gbp_refresh_token)
            locs = self.session.exec(
                select(ClientLocation).where(
                    ClientLocation.client_id == c.id,
                    ClientLocation.status == "active"
                )
            ).all()
            
            for loc in locs:
                if global_calls >= THROTTLE_GLOBAL_PER_RUN or per_client_calls >= THROTTLE_PER_CLIENT_PER_RUN:
                    break
                if not loc.gbp_location_name:
                    continue
                
                def _call_list():
                    return gbp.list_reviews(loc.gbp_location_name, page_size=50)
                
                try:
                    reviews = retry_call(
                        _call_list,
                        max_retries=GBP_MAX_RETRIES,
                        backoff_base=GBP_BACKOFF_BASE_SEC,
                        backoff_cap=GBP_BACKOFF_MAX_SEC,
                        should_retry=is_retryable_gbp_error,
                    )
                    global_calls += 1
                    per_client_calls += 1
                    
                    for gr in reviews:
                        existing = self.session.exec(
                            select(Review).where(Review.gbp_review_name == gr.gbp_review_name)
                        ).first()
                        
                        if not existing:
                            r = Review(
                                client_id=c.id,
                                location_id=loc.id,
                                gbp_review_name=gr.gbp_review_name,
                                reviewer_name=gr.reviewer_name,
                                rating=int(gr.rating),
                                comment=gr.comment or "",
                                review_time=gr.review_time,
                                has_reply=bool(gr.has_reply),
                                reply_text=gr.reply_text or "",
                                status="new" if not gr.has_reply else "posted",
                                meta={},
                            )
                            self.session.add(r)
                            created += 1
                        else:
                            existing.has_reply = bool(gr.has_reply)
                            existing.reply_text = gr.reply_text or ""
                            existing.updated_at = datetime.utcnow()
                            if existing.has_reply:
                                existing.status = "posted"
                            self.session.add(existing)
                            updated += 1
                    
                    self.session.commit()
                    
                except Exception as e:
                    errors += 1
                    if is_auth_error(e):
                        _create_or_bump_alert(
                            self.session,
                            severity="critical",
                            kind="gbp_auth",
                            message="Google access revoked. Reconnect.",
                            client_id=c.id,
                            location_id=loc.id,
                            meta={"error": str(e)[:300]},
                        )
                    elif is_quota_error(e):
                        _create_or_bump_alert(
                            self.session,
                            severity="warn",
                            kind="gbp_quota",
                            message="GBP quota hit. Throttled.",
                            client_id=c.id,
                            location_id=loc.id,
                        )
                    elif is_verified_location_error(e):
                        _create_or_bump_alert(
                            self.session,
                            severity="error",
                            kind="gbp_verification",
                            message="Location not verified.",
                            client_id=c.id,
                            location_id=loc.id,
                        )
        
        return {"ok": True, "created": created, "updated": updated, "errors": errors, "api_calls": global_calls}
    
    # -------- Draft --------
    def draft_new_reviews(self, batch: int = 30) -> Dict[str, Any]:
        drafted = 0
        needs_approval = 0
        skipped = 0
        
        reviews = self.session.exec(
            select(Review).where(
                Review.status == "new",
                Review.has_reply == False
            ).order_by(Review.created_at.asc()).limit(batch)
        ).all()
        
        for r in reviews:
            # Idempotency: skip if draft exists
            existing_draft = self.session.exec(
                select(ReplyDraft).where(ReplyDraft.review_id == r.id)
            ).first()
            if existing_draft:
                skipped += 1
                continue
            
            c = self.session.get(Client, r.client_id)
            if not c:
                r.status = "error"
                self.session.add(r)
                skipped += 1
                continue
            
            try:
                txt = draft_reply_llm(c.name, r.rating, r.comment or "")
            except Exception as e:
                r.status = "error"
                self.session.add(r)
                _create_or_bump_alert(
                    self.session,
                    severity="warn",
                    kind="openai",
                    message="Draft generation failed.",
                    client_id=c.id,
                    location_id=r.location_id,
                    meta={"error": str(e)[:300]},
                )
                skipped += 1
                continue
            
            needs = r.rating <= 3
            d = ReplyDraft(
                review_id=r.id,
                client_id=r.client_id,
                draft_text=txt,
                status="needs_approval" if needs else "approved",
                approved_by="" if needs else "system",
                approved_at=None if needs else datetime.utcnow(),
                meta={},
            )
            self.session.add(d)
            r.status = "needs_approval" if needs else "approved"
            self.session.add(r)
            drafted += 1
            if needs:
                needs_approval += 1
        
        self.session.commit()
        return {"ok": True, "drafted": drafted, "needs_approval": needs_approval, "skipped": skipped}
    
    # -------- Post --------
    def post_autopost(self, batch: int = 25) -> Dict[str, Any]:
        posted = 0
        skipped = 0
        errors = 0
        global_calls = 0
        
        drafts = self.session.exec(
            select(ReplyDraft).where(
                ReplyDraft.status == "approved"
            ).order_by(ReplyDraft.updated_at.asc()).limit(batch)
        ).all()
        
        for d in drafts:
            if global_calls >= THROTTLE_GLOBAL_PER_RUN:
                break
            
            r = self.session.get(Review, d.review_id)
            c = self.session.get(Client, d.client_id)
            
            if not r or not c or not c.gbp_refresh_token:
                d.status = "rejected"
                self.session.add(d)
                skipped += 1
                continue
            
            # Idempotency: skip if already has reply
            if r.has_reply or r.status == "posted":
                d.status = "posted"
                d.updated_at = datetime.utcnow()
                self.session.add(d)
                skipped += 1
                continue
            
            # Safety: only autopost 4-5 stars
            if r.rating < 4:
                skipped += 1
                continue
            
            gbp = GBPClient(refresh_token=c.gbp_refresh_token)
            
            def _call_post():
                return gbp.post_reply(r.gbp_review_name, d.draft_text)
            
            try:
                retry_call(
                    _call_post,
                    max_retries=GBP_MAX_RETRIES,
                    backoff_base=GBP_BACKOFF_BASE_SEC,
                    backoff_cap=GBP_BACKOFF_MAX_SEC,
                    should_retry=is_retryable_gbp_error,
                )
                global_calls += 1
                
                d.status = "posted"
                d.updated_at = datetime.utcnow()
                r.status = "posted"
                r.has_reply = True
                r.reply_text = d.draft_text
                r.updated_at = datetime.utcnow()
                self.session.add(d)
                self.session.add(r)
                self.session.commit()
                posted += 1
                
            except Exception as e:
                errors += 1
                d.meta = {**(d.meta or {}), "post_fail": str(e)[:300]}
                self.session.add(d)
                self.session.commit()
                
                if is_auth_error(e):
                    _create_or_bump_alert(
                        self.session,
                        severity="critical",
                        kind="gbp_auth",
                        message="Posting failed: auth revoked.",
                        client_id=c.id,
                        location_id=r.location_id,
                    )
                elif is_quota_error(e):
                    _create_or_bump_alert(
                        self.session,
                        severity="warn",
                        kind="gbp_quota",
                        message="Posting rate-limited.",
                        client_id=c.id,
                        location_id=r.location_id,
                    )
        
        return {"ok": True, "posted": posted, "skipped": skipped, "errors": errors, "api_calls": global_calls}
    
    # -------- Approve/Reject --------
    def approve_draft(self, draft_id: int, approved_by: str = "admin") -> None:
        d = self.session.get(ReplyDraft, draft_id)
        if not d:
            return
        
        d.status = "approved"
        d.approved_by = approved_by
        d.approved_at = datetime.utcnow()
        d.updated_at = datetime.utcnow()
        self.session.add(d)
        
        r = self.session.get(Review, d.review_id)
        if r:
            r.status = "approved"
            r.updated_at = datetime.utcnow()
            self.session.add(r)
        
        self.session.commit()
    
    def reject_draft(self, draft_id: int, reason: str = "") -> None:
        d = self.session.get(ReplyDraft, draft_id)
        if not d:
            return
        
        d.status = "rejected"
        d.updated_at = datetime.utcnow()
        d.meta = {**(d.meta or {}), "reason": reason}
        self.session.add(d)
        
        r = self.session.get(Review, d.review_id)
        if r:
            r.status = "skipped"
            r.updated_at = datetime.utcnow()
            self.session.add(r)
        
        self.session.commit()
    
    # -------- Weekly Report --------
    def weekly_report(self) -> Dict[str, Any]:
        week_end = datetime.utcnow()
        week_start = week_end - timedelta(days=7)
        
        clients = self.session.exec(
            select(Client).where(Client.status == "active")
        ).all()
        
        created = 0
        
        for c in clients:
            reviews = self.session.exec(
                select(Review).where(
                    Review.client_id == c.id,
                    Review.review_time != None,
                    Review.review_time >= week_start,
                    Review.review_time < week_end
                )
            ).all()
            
            total = len(reviews)
            stars = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            replied = 0
            pending = 0
            
            for r in reviews:
                stars[int(r.rating)] = stars.get(int(r.rating), 0) + 1
                if r.status == "posted":
                    replied += 1
                if r.status in ("needs_approval", "drafted"):
                    pending += 1
            
            md = f"""# Weekly Reputation Report — {c.name}

Window: {week_start.date().isoformat()} → {week_end.date().isoformat()}

## Volume
- New reviews: {total}
- Replied: {replied}
- Pending approval: {pending}

## Rating Breakdown
- 5★: {stars[5]}
- 4★: {stars[4]}
- 3★: {stars[3]}
- 2★: {stars[2]}
- 1★: {stars[1]}

## Notes
- 1–3★ replies require approval.
- 4–5★ can be autoposted.
""".strip()
            
            rep = WeeklyReport(
                client_id=c.id,
                week_start=week_start,
                week_end=week_end,
                summary_md=md,
                meta={"stars": stars, "replied": replied, "pending": pending, "total": total},
            )
            self.session.add(rep)
            created += 1
        
        self.session.commit()
        return {"ok": True, "reports_created": created}
