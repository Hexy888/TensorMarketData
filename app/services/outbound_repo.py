# Outbound Repository - Database Operations
# Minimal implementation for SQLModel

import re
from typing import Tuple, Optional
from sqlmodel import Session, select, or_, func
from app.models import OutboundTarget, OutboundEvent, OutboundOptout
from datetime import datetime, timedelta

FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com",
    "hotmail.com", "aol.com", "icloud.com",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_domain(domain_or_url: str | None) -> str | None:
    if not domain_or_url:
        return None
    d = domain_or_url.strip().lower()
    d = d.replace("https://", "").replace("http://", "")
    d = d.split("/")[0]
    d = d.split(":")[0]
    return d or None


def is_valid_business_email(email: str | None) -> bool:
    if not email:
        return False
    e = email.strip().lower()
    if not EMAIL_RE.match(e):
        return False
    dom = e.split("@")[-1]
    if dom in FREE_EMAIL_DOMAINS:
        return False
    return True


def email_domain(email: str) -> str:
    return email.strip().lower().split("@")[-1]


class OutboundRepo:
    """Database operations for outbound pipeline."""

    def __init__(self, session: Session):
        self.session = session

    # ---- Read ----

    def is_opted_out(self, *, email: str, domain: str) -> bool:
        """Check if email or domain is opted out."""
        result = self.session.exec(
            select(OutboundOptout).where(
                or_(
                    OutboundOptout.email_or_domain == email.lower(),
                    OutboundOptout.email_or_domain == domain.lower()
                )
            )
        ).first()
        return result is not None

    def has_target(self, *, email: str, domain: str) -> bool:
        """Dedupe check: email or domain already exists."""
        result = self.session.exec(
            select(OutboundTarget).where(
                or_(
                    OutboundTarget.contact_email == email.lower(),
                    func.lower(func.json_extract(OutboundTarget.website_url, '$.domain')) == domain.lower()
                )
            )
        ).first()
        return result is not None

    def count_events_today(self, *, event_type: str) -> int:
        """Count events of type today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.session.exec(
            select(func.count(OutboundEvent.id)).where(
                OutboundEvent.event_type == event_type,
                OutboundEvent.created_at >= today_start
            )
        ).first()
        return count or 0

    def fetch_queued_drafts(self, *, limit: int) -> list[dict]:
        """Return queued items with stored email draft."""
        targets = self.session.exec(
            select(OutboundTarget).where(
                OutboundTarget.status == "queued"
            ).limit(limit)
        ).all()
        
        results = []
        for t in targets:
            # Get latest draft from events
            draft_event = self.session.exec(
                select(OutboundEvent).where(
                    OutboundEvent.target_id == t.id,
                    OutboundEvent.event_type.in_(["queued", "draft"])
                ).order_by(OutboundEvent.created_at.desc())
            ).first()
            
            meta = {}
            if draft_event and draft_event.meta:
                import json
                try:
                    meta = json.loads(draft_event.meta)
                except:
                    pass
            
            results.append({
                "id": t.id,
                "company_name": t.company_name,
                "contact_email": t.contact_email,
                "website_domain": t.website_url,
                "first_name": "",  # Could extract from contact_email
                "draft_subject": meta.get("subject", ""),
                "draft_body": meta.get("body", ""),
                "variant": meta.get("variant", "A"),
            })
        return results

    def fetch_new_targets(self, *, limit: int) -> list[dict]:
        """Fetch targets with status=new."""
        targets = self.session.exec(
            select(OutboundTarget).where(
                OutboundTarget.status == "new"
            ).limit(limit)
        ).all()
        
        return [{
            "id": t.id,
            "company_name": t.company_name,
            "contact_email": t.contact_email,
            "website_domain": t.website_url,
            "first_name": "",
        } for t in targets]

    # ---- Write ----

    def insert_target(
        self,
        *,
        company_name: str,
        website_domain: str | None,
        city: str | None,
        state: str | None,
        contact_email: str,
        contact_role: str,
        source: str,
        notes: str | None = None,
    ) -> int:
        """Insert outbound_targets row and return target_id."""
        target = OutboundTarget(
            company_name=company_name,
            website_url=website_domain,
            location_city=city,
            location_state=state,
            contact_email=contact_email,
            contact_role=contact_role,
            source=source,
            notes=notes,
            status="new"
        )
        self.session.add(target)
        self.session.commit()
        return target.id

    def log_event(self, *, target_id: int, event_type: str, meta: dict) -> None:
        """Log an event."""
        import json
        event = OutboundEvent(
            target_id=target_id,
            event_type=event_type,
            meta=json.dumps(meta),
            created_at=datetime.utcnow()
        )
        self.session.add(event)
        self.session.commit()

    def mark_status(self, *, target_id: int, status: str) -> None:
        """Update target status."""
        target = self.session.get(OutboundTarget, target_id)
        if target:
            target.status = status
            self.session.add(target)
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
        """Persist draft to events table."""
        import json
        meta = json.dumps({
            "variant": variant,
            "subject": subject,
            "body": body,
            "personalization_used": personalization_used
        })
        event = OutboundEvent(
            target_id=target_id,
            event_type="draft",
            meta=meta,
            created_at=datetime.utcnow()
        )
        self.session.add(event)
        self.session.commit()

    def add_optout(self, *, email_or_domain: str, reason: str) -> None:
        """Add to opt-out list."""
        optout = OutboundOptout(
            email_or_domain=email_or_domain.strip().lower(),
            reason=reason
        )
        self.session.add(optout)
        self.session.commit()
