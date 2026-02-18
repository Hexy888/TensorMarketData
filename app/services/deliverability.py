# Deliverability Service - Warmup, caps, and rate management

from __future__ import annotations
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlmodel import Session, select, func

from app.models.autopilot import AutopilotState
from app.models.outbound import OutboundEvent

SEND_CAP_DAILY = int(os.getenv("SEND_CAP_DAILY", "20"))
SEND_CAP_MIN = int(os.getenv("SEND_CAP_MIN", "5"))
WARMUP_START_CAP = int(os.getenv("WARMUP_START_CAP", "5"))
WARMUP_DAYS = int(os.getenv("WARMUP_DAYS", "14"))
AUTOCAP_UP_STEP = int(os.getenv("AUTOCAP_UP_STEP", "2"))
AUTOCAP_DOWN_FACTOR = float(os.getenv("AUTOCAP_DOWN_FACTOR", "0.5"))
STOP_BOUNCE_PCT = float(os.getenv("AUTOPILOT_BOUNCE_STOP_PCT", "8"))
STOP_OPTOUT_PCT = float(os.getenv("AUTOPILOT_OPTOUT_STOP_PCT", "3"))


def _today_bounds() -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    start = datetime(year=now.year, month=now.month, day=now.day)
    end = start + timedelta(days=1)
    return start, end


def _get_state(session: Session, key: str) -> Optional[str]:
    row = session.exec(select(AutopilotState).where(AutopilotState.key == key)).first()
    return row.value if row else None


def _set_state(session: Session, key: str, value: str) -> None:
    row = session.exec(select(AutopilotState).where(AutopilotState.key == key)).first()
    if not row:
        row = AutopilotState(key=key, value=value)
    else:
        row.value = value
    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()


def get_dynamic_send_cap(session: Session) -> int:
    """Use dynamic cap if present; else fallback to SEND_CAP_DAILY."""
    v = _get_state(session, "send_cap_dynamic")
    if not v:
        return SEND_CAP_DAILY
    try:
        return int(v)
    except Exception:
        return SEND_CAP_DAILY


def _rates_today(session: Session) -> Dict[str, float]:
    start, end = _today_bounds()
    
    sent = session.exec(
        select(func.count(OutboundEvent.id)).where(
            OutboundEvent.event_type == "sent",
            OutboundEvent.created_at >= start,
            OutboundEvent.created_at < end
        )
    ).one() or 0
    
    bounce = session.exec(
        select(func.count(OutboundEvent.id)).where(
            OutboundEvent.event_type == "bounce",
            OutboundEvent.created_at >= start,
            OutboundEvent.created_at < end
        )
    ).one() or 0
    
    optout = session.exec(
        select(func.count(OutboundEvent.id)).where(
            OutboundEvent.event_type == "optout",
            OutboundEvent.created_at >= start,
            OutboundEvent.created_at < end
        )
    ).one() or 0
    
    sent_f = float(sent)
    return {
        "sent": sent_f,
        "bounce_pct": (float(bounce) / sent_f * 100.0) if sent_f else 0.0,
        "optout_pct": (float(optout) / sent_f * 100.0) if sent_f else 0.0,
    }


def _warmup_cap(session: Session) -> int:
    """Warmup day computed from stored start date."""
    start_iso = _get_state(session, "warmup_start_date")
    today = datetime.utcnow().date()
    
    if not start_iso:
        _set_state(session, "warmup_start_date", today.isoformat())
        day = 1
    else:
        try:
            start_date = datetime.fromisoformat(start_iso).date()
        except Exception:
            _set_state(session, "warmup_start_date", today.isoformat())
            start_date = today
        day = max((today - start_date).days + 1, 1)
    
    if day >= WARMUP_DAYS:
        return SEND_CAP_DAILY
    
    frac = (day - 1) / max(WARMUP_DAYS - 1, 1)
    cap = int(round(WARMUP_START_CAP + frac * (SEND_CAP_DAILY - WARMUP_START_CAP)))
    return max(min(cap, SEND_CAP_DAILY), SEND_CAP_MIN)


def recompute_dynamic_cap(session: Session) -> Dict[str, Any]:
    """Daily cap logic."""
    base = _warmup_cap(session)
    current = get_dynamic_send_cap(session)
    rates = _rates_today(session)
    
    # If rates are bad, reduce cap
    if rates["sent"] >= 20 and (rates["bounce_pct"] > STOP_BOUNCE_PCT or rates["optout_pct"] > STOP_OPTOUT_PCT):
        new_cap = max(int(current * AUTOCAP_DOWN_FACTOR), SEND_CAP_MIN)
        _set_state(session, "send_cap_dynamic", str(new_cap))
        return {"ok": True, "base": base, "prev": current, "new": new_cap, "reason": "rate_down", "rates": rates}
    
    # If healthy, allow increase
    if current < base:
        new_cap = min(current + AUTOCAP_UP_STEP, base)
        _set_state(session, "send_cap_dynamic", str(new_cap))
        return {"ok": True, "base": base, "prev": current, "new": new_cap, "reason": "rate_up", "rates": rates}
    
    # Align down if current exceeds base
    if current > base:
        _set_state(session, "send_cap_dynamic", str(base))
        return {"ok": True, "base": base, "prev": current, "new": base, "reason": "align_to_base", "rates": rates}
    
    _set_state(session, "send_cap_dynamic", str(current))
    return {"ok": True, "base": base, "prev": current, "new": current, "reason": "no_change", "rates": rates}
