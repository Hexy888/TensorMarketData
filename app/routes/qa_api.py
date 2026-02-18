from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from datetime import datetime
import os
import requests
from app.db import get_session
from app.tenant_models import AuditLog, Business, Subscription
from fastapi import Depends

router = APIRouter(prefix="/api")

LEGACY_TERMS = ["b2b", "lead", "replacement", "suppression", "icp"]

@router.get("/health")
def health(session: Session = Depends(get_session)):
    """
    Minimal health check for uptime monitors + OpenClaw.
    Returns info about the first business (for multi-tenant, returns first created).
    """
    # Get first business for health check (multi-tenant: returns first created)
    biz = session.exec(select(Business).order_by(Business.created_at.asc())).first()
    business_id = biz.id if biz else None
    
    sub = None
    if business_id:
        sub = session.exec(select(Subscription).where(Subscription.business_id == business_id)).first()
    
    return {
        "ok": True,
        "service": "tensormarketdata",
        "time_utc": datetime.utcnow().isoformat() + "Z",
        "db_ok": True,
        "business_present": bool(biz),
        "business_id": business_id,
        "subscription_present": bool(sub),
        "subscription_status": getattr(sub, "status", None) if sub else None,
    }

@router.get("/audit/recent")
def audit_recent(business_id: int | None = None, limit: int = 50, session: Session = Depends(get_session)):
    """
    Recent audit entries. Designed for OpenClaw verification.
    If business_id not provided, uses first business.
    """
    # Default to first business if not specified
    if business_id is None:
        biz = session.exec(select(Business).order_by(Business.created_at.asc())).first()
        business_id = biz.id if biz else 1
    
    limit = max(1, min(int(limit), 200))
    
    rows = session.exec(
        select(AuditLog)
        .where(AuditLog.business_id == business_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    
    return {
        "ok": True,
        "business_id": business_id,
        "count": len(rows),
        "items": [
            {
                "created_at": r.created_at.isoformat() + "Z" if r.created_at else None,
                "action": r.action,
                "detail": r.detail,
            }
            for r in rows
        ],
    }

@router.post("/pages/check")
def pages_check(base_url: str | None = None):
    """
    Checks critical public pages return 200 and confirms legacy terms do not appear.
    This runs server-side from Render so it sees true production content.
    """
    base = (base_url or os.getenv("APP_BASE_URL") or "https://tensormarketdata.com").rstrip("/")
    
    required_paths = [
        "/",
        "/pricing",
        "/how-it-works",
        "/faq",
        "/get-started",
        "/blog",
        "/contact",
        "/privacy",
        "/terms",
        "/login"
    ]
    
    results = []
    overall_ok = True
    found_legacy = []
    
    for p in required_paths:
        url = base + p
        try:
            r = requests.get(url, timeout=15)
            ok = (r.status_code == 200)
            text = (r.text or "").lower()
            hits = [t for t in LEGACY_TERMS if t in text]
            if hits:
                ok = False
                found_legacy.append({"path": p, "hits": hits})
            results.append({"path": p, "status_code": r.status_code, "ok": ok})
            overall_ok = overall_ok and ok
        except Exception as e:
            results.append({"path": p, "status_code": None, "ok": False, "error": str(e)})
            overall_ok = False
    
    return JSONResponse(
        {
            "ok": overall_ok,
            "base_url": base,
            "pages": results,
            "legacy_hits": found_legacy,
        }
    )
