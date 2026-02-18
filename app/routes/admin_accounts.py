# Admin Accounts Routes - CSV-based account intake

import os
import csv
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, Request, Form, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

ACCOUNTS_DIR = os.getenv("ACCOUNTS_DIR", "/Users/hexbornestudio/.openclaw/workspace/TensorMarketData-v2/data/accounts")
MASTER_CSV = os.path.join(ACCOUNTS_DIR, "accounts_master.csv")
OPS_TOKEN = os.getenv("OPS_TOKEN", "")

templates = Jinja2Templates(directory="templates")
router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    """Protect with X-Ops-Token header."""
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "unauthorized")
    return True


def _ensure_csv():
    os.makedirs(ACCOUNTS_DIR, exist_ok=True)
    if not os.path.exists(MASTER_CSV):
        with open(MASTER_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "company_name", "website_domain", "website_url", "city", "state",
                    "source", "gbp_url", "notes", "status", "updated_at"
                ],
            )
            w.writeheader()


def _normalize_domain(line: str) -> str:
    d = (line or "").strip().lower()
    d = d.replace("https://", "").replace("http://", "")
    d = d.replace("www.", "")
    d = d.split("/")[0].split(":")[0]
    return d


def _read_rows() -> List[Dict[str, str]]:
    _ensure_csv()
    with open(MASTER_CSV, "r", newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def _write_rows(rows: List[Dict[str, str]]) -> None:
    _ensure_csv()
    fieldnames = [
        "company_name", "website_domain", "website_url", "city", "state",
        "source", "gbp_url", "notes", "status", "updated_at"
    ]
    with open(MASTER_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: (r.get(k) or "") for k in fieldnames})


def _dedupe_set(rows: List[Dict[str, str]]) -> set:
    s = set()
    for r in rows:
        dom = _normalize_domain(r.get("website_domain") or "")
        if dom:
            s.add(dom)
    return s


@router.get("/admin/accounts", response_class=HTMLResponse)
def admin_accounts(request: Request, x_ops_token: str = Header(default="")):
    """Show accounts intake page."""
    if OPS_TOKEN and x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "unauthorized")
    
    rows = _read_rows()
    rows_view = list(reversed(rows))[:50]  # Show latest first
    
    return templates.TemplateResponse(
        "admin/accounts.html",
        {"request": request, "rows": rows_view, "message": "", "ok": True, "ops_token": OPS_TOKEN}
    )


@router.post("/admin/accounts", response_class=HTMLResponse)
def admin_accounts_post(request: Request, domains: str = Form(default=""), x_ops_token: str = Header(default="")):
    """Add domains from textarea."""
    if OPS_TOKEN and x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "unauthorized")
    
    rows = _read_rows()
    existing = _dedupe_set(rows)
    added = 0
    skipped = 0
    now = datetime.utcnow().isoformat()
    
    for line in (domains or "").splitlines():
        dom = _normalize_domain(line)
        if not dom:
            continue
        if dom in existing:
            skipped += 1
            continue
        
        rows.append({
            "company_name": "",
            "website_domain": dom,
            "website_url": f"https://{dom}",
            "city": "",
            "state": "",
            "source": "admin_intake",
            "gbp_url": "",
            "notes": "",
            "status": "new",
            "updated_at": now,
        })
        existing.add(dom)
        added += 1
    
    _write_rows(rows)
    rows_view = list(reversed(rows))[:50]
    
    msg = f"Added {added} new domains. Skipped {skipped} duplicates."
    return templates.TemplateResponse(
        "admin/accounts.html",
        {"request": request, "rows": rows_view, "message": msg, "ok": True, "ops_token": OPS_TOKEN}
    )
