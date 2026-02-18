# Outbound Repository - SQLModel Implementation

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlmodel import Session, select, func
from app.models.outbound import OutboundTarget, OutboundEvent, OutboundOptout


def _today_utc_bounds() -> tuple[datetime, datetime]:
    """Use UTC day boundaries for cron."""
    now = datetime.utcnow()
    start = datetime(year=now.year, month=now.month, day=now.day)
    end = start + timedelta(days=1)
    return start, end


class OutboundRepoSQLModel:
    """Concrete implementation for OutboundPipeline."""

    def __init__(self, session: Session):
        self.session = session

    # --------------------
    # READ
    # --------------------
    def is_opted_out(self, *, email: str, domain: str) -> bool:
        email = (email or "").strip().lower()
        domain = (domain or "").strip().lower()
        if not email and not domain:
            return False
        
        q = select(OutboundOptout).where(
            (OutboundOptout.email_or_domain == email) |
            (OutboundOptout.email_or_domain == domain)
        )
        return self.session.exec(q).first() is not None

    def has_target(self, *, email: str, domain: str) -> bool:
        email = email.strip().lower()
        domain = (domain or "").strip().lower()
        
        q = select(OutboundTarget.id).where(OutboundTarget.contact_email == email)
        if domain:
            q = q.where(OutboundTarget.website_domain == domain)
        return self.session.exec(q).first() is not None

    def count_events_today(self, *, event_type: str) -> int:
        start, end = _today_utc_bounds()
        q = (
            select(func.count(OutboundEvent.id))
            .where(OutboundEvent.event_type == event_type)
            .where(OutboundEvent.created_at >= start)
            .where(OutboundEvent.created_at < end)
        )
        return int(self.session.exec(q).one() or 0)

    def fetch_new_targets(self, *, limit: int = 200) -> List[Dict[str, Any]]:
        """Targets inserted (new) but not drafted yet."""
        q = (
            select(OutboundTarget)
            .where(OutboundTarget.status == "new")
            .order_by(OutboundTarget.created_at.asc())
            .limit(limit)
        )
        rows = self.session.exec(q).all()
        return [
            {
                "id": r.id,
                "company_name": r.company_name,
                "contact_email": r.contact_email,
                "website_domain": r.website_domain,
                "first_name": r.first_name,
            }
            for r in rows if r.id is not None
        ]

    def fetch_queued_drafts(self, *, limit: int) -> List[Dict[str, Any]]:
        """Targets that are queued and have draft fields present."""
        q = (
            select(OutboundTarget)
            .where(OutboundTarget.status == "queued")
            .where(OutboundTarget.draft_subject.is_not(None))
            .where(OutboundTarget.draft_body.is_not(None))
            .order_by(OutboundTarget.updated_at.asc())
            .limit(limit)
        )
        rows = self.session.exec(q).all()
        
        out: List[Dict[str, Any]] = []
        for r in rows:
            if r.id is None:
                continue
            out.append({
                "id": r.id,
                "company_name": r.company_name,
                "contact_email": r.contact_email,
                "website_domain": r.website_domain,
                "draft_subject": r.draft_subject,
                "draft_body": r.draft_body,
                "draft_variant": r.draft_variant,
            })
        return out

    # --------------------
    # WRITE
    # --------------------
    def insert_target(
        self,
        *,
        company_name: str,
        website_domain: Optional[str],
        city: Optional[str],
        state: Optional[str],
        contact_email: str,
        contact_role: str,
        source: str,
        notes: Optional[str] = None,
    ) -> int:
        row = OutboundTarget(
            company_name=company_name.strip(),
            website_domain=(website_domain or None),
            location_city=city,
            location_state=state,
            contact_email=contact_email.strip().lower(),
            contact_role=(contact_role or "unknown"),
            source=(source or "manual"),
            notes=notes,
            status="new",
            updated_at=datetime.utcnow(),
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        assert row.id is not None
        return row.id

    def log_event(self, *, target_id: int, event_type: str, meta: Dict[str, Any]) -> None:
        ev = OutboundEvent(target_id=target_id, event_type=event_type, meta=meta or {})
        self.session.add(ev)
        self.session.commit()

    def mark_status(self, *, target_id: int, status: str) -> None:
        row = self.session.get(OutboundTarget, target_id)
        if not row:
            return
        row.status = status
        row.updated_at = datetime.utcnow()
        self.session.add(row)
        self.session.commit()

    def store_email_draft(
        self,
        *,
        target_id: int,
        variant: str,
        subject: str,
        body: str,
        personalization_used: bool,
    ) -> None:
        row = self.session.get(OutboundTarget, target_id)
        if not row:
            return
        row.draft_variant = variant
        row.draft_subject = subject
        row.draft_body = body
        row.draft_personalization_used = bool(personalization_used)
        row.updated_at = datetime.utcnow()
        self.session.add(row)
        self.session.commit()

    def add_optout(self, *, email_or_domain: str, reason: str) -> None:
        key = email_or_domain.strip().lower()
        if not key:
            return
        existing = self.session.exec(
            select(OutboundOptout).where(OutboundOptout.email_or_domain == key)
        ).first()
        if existing:
            return
        row = OutboundOptout(email_or_domain=key, reason=reason)
        self.session.add(row)
        self.session.commit()
