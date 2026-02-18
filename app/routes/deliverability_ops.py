# Deliverability Operations Routes

from __future__ import annotations
import os
from typing import List
import dns.resolver
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.services.deliverability import recompute_dynamic_cap

OPS_TOKEN = os.getenv("OPS_TOKEN", "")
SENDING_DOMAIN = os.getenv("SENDING_DOMAIN", "tensormarketdata.com")

router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


def _txt(name: str) -> List[str]:
    try:
        ans = dns.resolver.resolve(name, "TXT")
        out = []
        for r in ans:
            out.append("".join([p.decode() if isinstance(p, bytes) else str(p) for p in r.strings]))
        return out
    except Exception:
        return []


def _mx(name: str) -> List[str]:
    try:
        ans = dns.resolver.resolve(name, "MX")
        return [str(r.exchange).rstrip(".") for r in ans]
    except Exception:
        return []


@router.post("/api/ops/deliverability/recompute_caps")
def ops_recompute_caps(ok=Depends(require_ops), session: Session = Depends(get_session)):
    """Recompute dynamic send cap based on rates."""
    return recompute_dynamic_cap(session)


@router.post("/api/ops/deliverability/check_dns")
def ops_check_dns(ok=Depends(require_ops)):
    """Check sender domain DNS for outbound readiness."""
    spf_txt = _txt(SENDING_DOMAIN)
    dmarc_txt = _txt(f"_dmarc.{SENDING_DOMAIN}")
    dkim_txt = _txt(f"google._domainkey.{SENDING_DOMAIN}")
    mx = _mx(SENDING_DOMAIN)
    
    spf_ok = any("v=spf1" in t.lower() for t in spf_txt)
    dmarc_ok = any(t.lower().startswith("v=dmarc1") for t in dmarc_txt)
    dkim_ok = len(dkim_txt) > 0
    mx_ok = len(mx) > 0
    
    return {
        "ok": True,
        "domain": SENDING_DOMAIN,
        "spf_ok": spf_ok,
        "spf_records": spf_txt,
        "dmarc_ok": dmarc_ok,
        "dmarc_records": dmarc_txt,
        "dkim_google_selector_ok": dkim_ok,
        "dkim_google_selector_records": dkim_txt,
        "mx_ok": mx_ok,
        "mx": mx,
        "note": "If DKIM selector is not 'google', update selector name accordingly.",
    }
