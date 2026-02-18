# Outbound Growth Service
# Handles list building, verification, copying, sending, and response handling
import os
import json
import re
from datetime import datetime, timedelta
from sqlmodel import Session, select, or_, and_
from app.models.outbound import OutboundTarget, OutboundEvent, OutboundOptout
from app.services.outbound_templates import (
    VARIANT_A_SUBJECT, VARIANT_A_BODY,
    VARIANT_B_SUBJECT, VARIANT_B_BODY,
    VARIANT_C_SUBJECT, VARIANT_C_BODY,
    FOLLOWUP_2_SUBJECT, FOLLOWUP_2_BODY,
    FOLLOWUP_3_SUBJECT, FOLLOWUP_3_BODY,
    RESPONSE_INTERESTED_SUBJECT, RESPONSE_INTERESTED_BODY,
    RESPONSE_QUESTIONS_SUBJECT, RESPONSE_QUESTIONS_BODY,
    RESPONSE_OPTOUT_SUBJECT, RESPONSE_OPTOUT_BODY,
    PHYSICAL_ADDRESS,
)

SEND_CAP_DAILY = int(os.getenv("SEND_CAP_DAILY", "20"))

def log_event(session: Session, target_id: int, event_type: str, meta: dict = None):
    session.add(OutboundTarget(
        target_id=target_id,
        event_type=event_type,
        meta=json.dumps(meta or {}),
        created_at=datetime.utcnow()
    ))
    session.commit()

def add_target(session: Session, company_name: str, website_url: str, city: str, state: str,
               contact_email: str, contact_role: str = "unknown", owner_name: str = None,
               gbp_url: str = None, source: str = "manual", notes: str = None) -> OutboundTarget:
    target = OutboundTarget(
        company_name=company_name,
        website_url=website_url,
        location_city=city,
        location_state=state,
        contact_email=contact_email,
        contact_role=contact_role,
        owner_name=owner_name,
        gbp_url=gbp_url,
        source=source,
        notes=notes,
        status="new"
    )
    session.add(target)
    session.commit()
    session.refresh(target)
    log_event(session, target.id, "created", {"source": source})
    return target

def verify_and_queue(session: Session) -> dict:
    """Verify emails and move to queued status."""
    targets = session.exec(select(OutboundTarget).where(OutboundTarget.status == "new")).all()
    
    queued = 0
    skipped = 0
    opted_out = 0
    
    # Get opt-out domains/emails
    optouts = session.exec(select(OutboundOptout)).all()
    optout_set = {o.email_or_domain for o in optouts}
    optout_domains = {o.split('@')[1] if '@' in o else o for o in optout_set}
    
    for t in targets:
        email = t.contact_email.lower()
        
        # Skip personal email domains
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        domain = email.split('@')[1] if '@' in email else ""
        if domain in personal_domains:
            t.status = "bounced"
            session.add(t)
            skipped += 1
            continue
        
        # Check opt-outs
        if email in optout_set or domain in optout_domains:
            t.status = "opted_out"
            session.add(t)
            log_event(session, t.id, "auto_optout", {"reason": "in_optout_list"})
            opted_out += 1
            continue
        
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            t.status = "bounced"
            session.add(t)
            skipped += 1
            continue
        
        # Check duplicate domain in queued/sent
        existing = session.exec(
            select(OutboundTarget).where(
                OutboundTarget.contact_email.ilike(f"%{domain}%"),
                OutboundTarget.status.in_(["queued", "sent", "replied", "converted"])
            )
        ).first()
        if existing:
            skipped += 1
            continue
        
        # Queue it
        t.status = "queued"
        session.add(t)
        log_event(session, t.id, "queued", {})
        queued += 1
    
    session.commit()
    return {"queued": queued, "skipped": skipped, "opted_out": opted_out}

def generate_personalization(website_url: str, city: str, state: str) -> str:
    """Generate one-line personalization based on website."""
    # Simple heuristic - in production, would scrape the website
    return f"Saw you're serving the {city}, {state} area."

def prepare_emails(session: Session, variant: str = "A") -> int:
    """Generate email drafts for queued targets."""
    targets = session.exec(
        select(OutboundTarget).where(OutboundTarget.status == "queued")
    ).all()
    
    prepared = 0
    for t in targets:
        # Check if already has queued email
        existing = session.exec(
            select(OutboundEvent).where(
                OutboundEvent.target_id == t.id,
                OutboundEvent.event_type == "queued"
            )
        ).first()
        if existing:
            continue
        
        first_name = t.owner_name.split()[0] if t.owner_name else "Team"
        company = t.company_name
        
        personalization = ""
        if t.website_url:
            personalization = generate_personalization(t.website_url, t.location_city, t.location_state)
        
        # Select variant
        if variant == "A":
            subject = VARIANT_A_SUBJECT.format(company=company)
            body = VARIANT_A_BODY.format(first_or_team=first_name, personalization_line=personalization)
        elif variant == "B":
            subject = VARIANT_B_SUBJECT.format(company=company)
            body = VARIANT_B_BODY.format(first_or_team=first_name, personalization_line=personalization)
        else:
            subject = VARIANT_C_SUBJECT.format(company=company)
            body = VARIANT_C_BODY.format(first_or_team=first_name, personalization_line=personalization)
        
        body += f"\nAddress: {PHYSICAL_ADDRESS}"
        
        meta = {
            "variant": variant,
            "subject": subject,
            "body": body,
            "personalization_used": bool(personalization)
        }
        
        log_event(session, t.id, "queued", meta)
        prepared += 1
    
    return prepared

def send_emails(session: Session) -> dict:
    """Send emails up to daily cap."""
    targets = session.exec(
        select(OutboundTarget).where(OutboundTarget.status == "queued")
    ).all()
    
    sent = 0
    bounced = 0
    
    for t in targets[:SEND_CAP_DAILY]:
        # Get queued event
        event = session.exec(
            select(OutboundEvent).where(
                OutboundEvent.target_id == t.id,
                OutboundEvent.event_type == "queued"
            )
        ).first()
        
        if not event:
            continue
        
        meta = json.loads(event.meta)
        
        # Send via email service
        from app.services.email_tx import send_template
        from app.services.email_smtp import send_smtp_email
        
        try:
            # Simple send (would use proper SMTP in production)
            success = send_smtp_email(
                t.contact_email,
                meta.get("subject", "Quick question"),
                f"<pre>{meta.get('body', '')}</pre>"
            )
            
            if success:
                t.status = "sent"
                session.add(t)
                log_event(session, t.id, "sent", {"variant": meta.get("variant")})
                sent += 1
            else:
                t.status = "bounced"
                session.add(t)
                log_event(session, t.id, "bounce", {"error": "smtp_failed"})
                bounced += 1
        except Exception as e:
            t.status = "bounced"
            session.add(t)
            log_event(session, t.id, "bounce", {"error": str(e)[:200]})
            bounced += 1
    
    session.commit()
    return {"sent": sent, "bounced": bounced, "cap": SEND_CAP_DAILY}

def classify_reply(session: Session, reply_text: str, target_id: int = None) -> str:
    """Classify a reply into category."""
    text = reply_text.lower().strip()
    
    # Interested
    if any(x in text for x in ['yes', 'send link', 'tell me more', 'interested', 'how does it work', 'what do you need']):
        return "interested"
    
    # Opt-out
    if any(x in text for x in ['opt out', 'remove', 'unsubscribe', 'don\'t contact', 'stop']):
        return "optout"
    
    # Not now
    if any(x in text for x in ['later', 'busy', 'not now', 'right now']):
        return "notnow"
    
    # Questions
    if '?' in text or any(x in text for x in ['how', 'what', 'can you', 'do you']):
        return "questions"
    
    return "unknown"

def handle_reply(session: Session, reply_text: str, from_email: str) -> dict:
    """Handle an incoming reply to outbound email."""
    # Find target
    target = session.exec(
        select(OutboundTarget).where(
            OutboundTarget.contact_email.ilike(f"%{from_email}%")
        )
    ).first()
    
    if not target:
        return {"action": "unknown_target", "email": from_email}
    
    category = classify_reply(session, reply_text, target.id)
    
    if category == "interested":
        target.status = "replied"
        session.add(target)
        log_event(session, target.id, "reply", {"type": "interested"})
        
        # Send onboarding link
        send_smtp_email(
            target.contact_email,
            RESPONSE_INTERESTED_SUBJECT,
            f"<pre>{RESPONSE_INTERESTED_BODY}</pre>"
        )
        
    elif category == "optout":
        target.status = "opted_out"
        session.add(target)
        
        # Add to optouts
        optout = OutboundOptout(email_or_domain=target.contact_email, reason="manual_reply")
        session.add(optout)
        log_event(session, target.id, "reply", {"type": "optout"})
        
        # Confirm
        send_smtp_email(
            target.contact_email,
            RESPONSE_OPTOUT_SUBJECT,
            f"<pre>{RESPONSE_OPTOUT_BODY}</pre>"
        )
        
    elif category == "questions":
        target.status = "replied"
        session.add(target)
        log_event(session, target.id, "reply", {"type": "questions"})
        
        send_smtp_email(
            target.contact_email,
            RESPONSE_QUESTIONS_SUBJECT,
            f"<pre>{RESPONSE_QUESTIONS_BODY}</pre>"
        )
        
    elif category == "notnow":
        target.status = "replied"
        session.add(target)
        log_event(session, target.id, "reply", {"type": "notnow", "action": "tag_later"})
    
    session.commit()
    return {"action": category, "target_id": target.id}

def get_weekly_stats(session: Session) -> dict:
    """Get weekly statistics for the analyst."""
    since = datetime.utcnow() - timedelta(days=7)
    
    # Counts
    sent = session.exec(
        select(OutboundEvent).where(
            OutboundEvent.event_type == "sent",
            OutboundEvent.created_at >= since
        )
    ).count()
    
    replies = session.exec(
        select(OutboundEvent).where(
            OutboundEvent.event_type == "reply",
            OutboundEvent.created_at >= since
        )
    ).count()
    
    optouts = session.exec(
        select(OutboundEvent).where(
            OutboundEvent.event_type == "optout",
            OutboundEvent.created_at >= since
        )
    ).count()
    
    bounces = session.exec(
        select(OutboundEvent).where(
            OutboundEvent.event_type == "bounce",
            OutboundEvent.created_at >= since
        )
    ).count()
    
    conversions = session.exec(
        select(OutboundTarget).where(
            OutboundTarget.status == "converted",
            OutboundTarget.created_at >= since
        )
    ).count()
    
    delivered = sent - bounces if sent > bounces else 0
    reply_rate = (replies / delivered * 100) if delivered > 0 else 0
    optout_rate = (optouts / delivered * 100) if delivered > 0 else 0
    bounce_rate = (bounces / sent * 100) if sent > 0 else 0
    
    return {
        "sent": sent,
        "replies": replies,
        "optouts": optouts,
        "bounces": bounces,
        "conversions": conversions,
        "delivered": delivered,
        "reply_rate": round(reply_rate, 2),
        "optout_rate": round(optout_rate, 2),
        "bounce_rate": round(bounce_rate, 2),
    }
