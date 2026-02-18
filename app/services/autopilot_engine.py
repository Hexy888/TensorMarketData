# Autopilot Engine - Autonomous follow-up scheduling

from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlmodel import Session, select, func

from app.models.autopilot import AutopilotTask, AutopilotState
from app.models.outbound import OutboundTarget, OutboundEvent, OutboundOptOut
from app.services.email_sender import send_email_smtp
from app.services.outbound_repo_sql import OutboundRepoSQLModel

SEND_CAP_DAILY = int(os.getenv("SEND_CAP_DAILY", "20"))
FU1_DAYS = int(os.getenv("FU1_DAYS", "2"))
FU2_DAYS = int(os.getenv("FU2_DAYS", "5"))
FU3_DAYS = int(os.getenv("FU3_DAYS", "10"))
SNOOZE_DAYS = int(os.getenv("SNOOZE_DAYS", "21"))
STOP_BOUNCE_PCT = float(os.getenv("AUTOPILOT_BOUNCE_STOP_PCT", "8"))
STOP_OPTOUT_PCT = float(os.getenv("AUTOPILOT_OPTOUT_STOP_PCT", "3"))
PAUSE_HOURS = int(os.getenv("AUTOPILOT_PAUSE_HOURS", "24"))


def _today_utc_bounds() -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    start = datetime(year=now.year, month=now.month, day=now.day)
    end = start + timedelta(days=1)
    return start, end


def _normalize_domain(domain: str) -> str:
    d = (domain or "").strip().lower()
    d = d.replace("https://", "").replace("http://", "")
    d = d.replace("www.", "")
    d = d.split("/")[0].split(":")[0]
    return d


def _email_domain(email: str) -> str:
    return email.strip().lower().split("@")[-1]


def _get_pause_until(session: Session) -> Optional[datetime]:
    row = session.exec(
        select(AutopilotState).where(AutopilotState.key == "pause_until")
    ).first()
    if not row or not row.value:
        return None
    try:
        return datetime.fromisoformat(row.value)
    except Exception:
        return None


def _set_pause_until(session: Session, until: datetime, reason: str) -> None:
    row = session.exec(
        select(AutopilotState).where(AutopilotState.key == "pause_until")
    ).first()
    if not row:
        row = AutopilotState(key="pause_until", value=until.isoformat())
    else:
        row.value = until.isoformat()
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()


def _rates_today(session: Session) -> Dict[str, float]:
    """Compute bounce + optout rates vs sent count for today."""
    start, end = _today_utc_bounds()
    
    sent = session.exec(
        select(func.count(OutboundEvent.id)).where(
            OutboundEvent.event_type == "sent",
            OutboundEvent.created_at >= start,
            OutboundEvent.created_at < end
        )
    ).one() or 0
    
    bounces = session.exec(
        select(func.count(OutboundEvent.id)).where(
            OutboundEvent.event_type == "bounce",
            OutboundEvent.created_at >= start,
            OutboundEvent.created_at < end
        )
    ).one() or 0
    
    optouts = session.exec(
        select(func.count(OutboundEvent.id)).where(
            OutboundEvent.event_type == "optout",
            OutboundEvent.created_at >= start,
            OutboundEvent.created_at < end
        )
    ).one() or 0
    
    sent = float(sent)
    return {
        "sent": sent,
        "bounce_pct": (float(bounces) / sent * 100.0) if sent else 0.0,
        "optout_pct": (float(optouts) / sent * 100.0) if sent else 0.0,
    }


def _create_followup_tasks(session: Session, target_id: int) -> None:
    """Create FU tasks once after the initial send."""
    exists = session.exec(
        select(AutopilotTask).where(
            AutopilotTask.target_id == target_id,
            AutopilotTask.task_type == "followup_1"
        )
    ).first()
    if exists:
        return
    
    now = datetime.utcnow()
    tasks = [
        AutopilotTask(
            target_id=target_id,
            task_type="followup_1",
            due_at=now + timedelta(days=FU1_DAYS)
        ),
        AutopilotTask(
            target_id=target_id,
            task_type="followup_2",
            due_at=now + timedelta(days=FU2_DAYS)
        ),
        AutopilotTask(
            target_id=target_id,
            task_type="followup_3",
            due_at=now + timedelta(days=FU3_DAYS)
        ),
    ]
    for t in tasks:
        session.add(t)
    session.commit()


def _cancel_pending_tasks(session: Session, target_id: int) -> None:
    tasks = session.exec(
        select(AutopilotTask).where(
            AutopilotTask.target_id == target_id,
            AutopilotTask.status == "pending"
        )
    ).all()
    for t in tasks:
        t.status = "canceled"
        t.updated_at = datetime.utcnow()
        session.add(t)
    session.commit()


def _is_opted_out(session: Session, email: str, domain: str) -> bool:
    result = session.exec(
        select(OutboundOptOut).where(
            (OutboundOptOut.email_or_domain == email.strip().lower()) |
            (OutboundOptOut.email_or_domain == domain.strip().lower())
        )
    ).first()
    return result is not None


def _followup_copy(task_type: str, company: str) -> tuple[str, str]:
    """Short, safe follow-up. No claims, no pressure."""
    if task_type == "followup_1":
        subj = f"Re: reviews for {company}"
        body = (
            f"Hi — quick bump.\n"
            f"If you want TensorMarketData to handle review monitoring + drafted replies (approval for 1–3★), reply YES.\n"
            f"If not, reply opt out.\n"
        )
        return subj, body
    
    if task_type == "followup_2":
        subj = f"Should I close this out, {company}?"
        body = (
            f"Hi — checking once more.\n"
            f"We can run approval-gated review replies so nothing sensitive posts without you.\n"
            f"Reply YES for onboarding, or opt out.\n"
        )
        return subj, body
    
    # followup_3 or snooze_followup
    subj = f"Last note — TensorMarketData"
    body = (
        f"Last note from me.\n"
        f"If reputation ops help this quarter, reply YES and I'll send the setup link.\n"
        f"Otherwise reply opt out.\n"
    )
    return subj, body


class AutopilotEngine:
    def __init__(self, session: Session):
        self.session = session
        self.repo = OutboundRepoSQLModel(session)

    def on_initial_sent(self, target_id: int):
        """Hook: call when logging a 'sent' event."""
        _create_followup_tasks(self.session, target_id)

    def run_due_tasks(self) -> Dict[str, Any]:
        """Main: run scheduled follow-up tasks."""
        
        # Pause check
        pause_until = _get_pause_until(self.session)
        if pause_until and pause_until > datetime.utcnow():
            return {"ok": True, "paused": True, "pause_until": pause_until.isoformat()}
        
        # Deliverability stop rules
        rates = _rates_today(self.session)
        if rates["sent"] >= 20:
            if rates["bounce_pct"] > STOP_BOUNCE_PCT or rates["optout_pct"] > STOP_OPTOUT_PCT:
                until = datetime.utcnow() + timedelta(hours=PAUSE_HOURS)
                _set_pause_until(self.session, until, reason="rate_stop")
                return {
                    "ok": True,
                    "paused": True,
                    "reason": "rate_stop",
                    "rates": rates,
                    "pause_until": until.isoformat()
                }
        
        # Cap remaining for today
        sent_today = self.repo.count_events_today(event_type="sent")
        remaining = max(SEND_CAP_DAILY - sent_today, 0)
        
        if remaining <= 0:
            return {"ok": True, "sent": 0, "reason": "send cap reached"}
        
        # Fetch due tasks
        now = datetime.utcnow()
        tasks = self.session.exec(
            select(AutopilotTask)
            .where(AutopilotTask.status == "pending", AutopilotTask.due_at <= now)
            .order_by(AutopilotTask.due_at.asc())
            .limit(remaining)
        ).all()
        
        sent = 0
        skipped = 0
        consecutive_errors = 0
        
        for t in tasks:
            target = self.session.get(OutboundTarget, t.target_id)
            if not target:
                t.status = "skipped"
                t.updated_at = now
                self.session.add(t)
                self.session.commit()
                skipped += 1
                continue
            
            # Stop if target in terminal state
            if target.status in ("opted_out", "bounced", "converted", "qualified"):
                t.status = "canceled"
                t.updated_at = now
                self.session.add(t)
                self.session.commit()
                skipped += 1
                continue
            
            # Opt-out guard
            email = target.contact_email.strip().lower()
            dom = _normalize_domain(target.website_domain) or _email_domain(email)
            if _is_opted_out(self.session, email=email, domain=dom):
                target.status = "opted_out"
                target.updated_at = now
                self.session.add(target)
                t.status = "canceled"
                t.updated_at = now
                self.session.add(t)
                self.session.commit()
                skipped += 1
                continue
            
            # Compose follow-up
            subject, body = _followup_copy(t.task_type, target.company_name or "your team")
            
            try:
                send_email_smtp(to_email=email, subject=subject, body_text=body)
                
                # Log + update
                self.session.add(OutboundEvent(
                    target_id=target.id,
                    event_type="sent",
                    meta={"autopilot": True, "task": t.task_type}
                ))
                target.status = "sent"
                target.updated_at = now
                t.status = "done"
                t.updated_at = now
                self.session.add(target)
                self.session.add(t)
                self.session.commit()
                sent += 1
                consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                self.session.add(OutboundEvent(
                    target_id=target.id,
                    event_type="bounce",
                    meta={"error": str(e)[:300], "autopilot": True, "task": t.task_type}
                ))
                target.status = "bounced"
                target.updated_at = now
                t.status = "done"
                t.updated_at = now
                self.session.add(target)
                self.session.add(t)
                self.session.commit()
                
                if consecutive_errors >= 3:
                    break
        
        return {"ok": True, "sent": sent, "skipped": skipped, "rates": rates}

    def route_reply(self, target_id: int, classification: str):
        """Map reply to statuses + follow-up cancellation."""
        target = self.session.get(OutboundTarget, target_id)
        if not target:
            return
        
        now = datetime.utcnow()
        
        if classification == "yes":
            target.status = "qualified"
            _cancel_pending_tasks(self.session, target_id)
            
        elif classification == "question":
            target.status = "needs_answer"
            _cancel_pending_tasks(self.session, target_id)
            
        elif classification == "later":
            target.status = "snoozed"
            _cancel_pending_tasks(self.session, target_id)
            # Create snooze followup
            snooze = AutopilotTask(
                target_id=target_id,
                task_type="snooze_followup",
                due_at=now + timedelta(days=SNOOZE_DAYS),
                status="pending"
            )
            self.session.add(snooze)
            
        elif classification == "optout":
            target.status = "opted_out"
            _cancel_pending_tasks(self.session, target_id)
            
        else:
            target.status = "replied"
            _cancel_pending_tasks(self.session, target_id)
        
        target.updated_at = now
        self.session.add(target)
        self.session.commit()
