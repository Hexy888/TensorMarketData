# Accounts Operations - CSV-based account processing

from __future__ import annotations
import os
import csv
from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session
from app.db import get_session
from app.services.outbound_repo_sql import OutboundRepoSQLModel
from app.services.outbound_pipeline import OutboundPipeline
from app.integrations.apollo_client import ApolloClient

OPS_TOKEN = os.getenv("OPS_TOKEN", "")
ACCOUNTS_DIR = os.getenv("ACCOUNTS_DIR", "/Users/hexbornestudio/.openclaw/workspace/TensorMarketData-v2/data/accounts")
MASTER_CSV = os.path.join(ACCOUNTS_DIR, "accounts_master.csv")
ACCOUNTS_PER_RUN = int(os.getenv("ACCOUNTS_PER_RUN", "30"))

router = APIRouter()


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


def _ensure_master_csv() -> None:
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


def _read_accounts() -> List[Dict[str, str]]:
    _ensure_master_csv()
    with open(MASTER_CSV, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]


def _write_accounts(rows: List[Dict[str, str]]) -> None:
    _ensure_master_csv()
    fieldnames = [
        "company_name", "website_domain", "website_url", "city", "state",
        "source", "gbp_url", "notes", "status", "updated_at"
    ]
    with open(MASTER_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {k: (r.get(k) or "") for k in fieldnames}
            w.writerow(out)


def _normalize_domain(domain: str) -> str:
    d = (domain or "").strip().lower()
    d = d.replace("https://", "").replace("http://", "")
    d = d.replace("www.", "")
    d = d.split("/")[0].split(":")[0]
    return d


@router.post("/api/ops/outbound/accounts_process")
def accounts_process(
    ok=Depends(require_ops),
    session: Session = Depends(get_session)
):
    """
    Process up to ACCOUNTS_PER_RUN accounts (status=new), feeding each domain into Apollo enrichment.
    Enrichment credit cap is enforced inside OutboundPipeline.enrich_and_insert_daily().
    """
    repo = OutboundRepoSQLModel(session)
    pipe = OutboundPipeline(repo=repo)

    rows = _read_accounts()

    # Select new rows with a domain
    candidates = []
    for idx, r in enumerate(rows):
        status = (r.get("status") or "new").strip().lower()
        dom = _normalize_domain(r.get("website_domain") or "")
        if status == "new" and dom:
            candidates.append((idx, r, dom))

    candidates = candidates[:ACCOUNTS_PER_RUN]

    summary = {
        "ok": True,
        "master_csv": MASTER_CSV,
        "accounts_seen_new": len(candidates),
        "accounts_processed": 0,
        "shells_total": 0,
        "enriched_total": 0,
        "inserted_total": 0,
        "stopped_reason": None,
    }

    if not candidates:
        return {**summary, "stopped_reason": "no new accounts"}

    for idx, r, dom in candidates:
        # Run search shells for this domain
        try:
            shells = pipe.apollo_search_shells(company_name=None, domain=dom, limit=50)
        except Exception as e:
            rows[idx]["status"] = "skipped"
            rows[idx]["updated_at"] = datetime.utcnow().isoformat()
            rows[idx]["notes"] = (rows[idx].get("notes") or "") + f" | search_err:{str(e)[:120]}"
            continue

        summary["shells_total"] += len(shells)

        # Attempt enrichment insert
        try:
            res = pipe.enrich_and_insert_daily(shells)
        except Exception as e:
            rows[idx]["status"] = "skipped"
            rows[idx]["updated_at"] = datetime.utcnow().isoformat()
            rows[idx]["notes"] = (rows[idx].get("notes") or "") + f" | enrich_err:{str(e)[:120]}"
            continue

        summary["accounts_processed"] += 1
        summary["enriched_total"] += int(res.get("enriched", 0))
        summary["inserted_total"] += int(res.get("inserted", 0))

        # Mark processed
        rows[idx]["status"] = "processed"
        rows[idx]["updated_at"] = datetime.utcnow().isoformat()

        # If cap hit, stop early
        if res.get("reason") == "enrich cap reached":
            summary["stopped_reason"] = "enrich cap reached"
            break

    _write_accounts(rows)

    if not summary["stopped_reason"]:
        summary["stopped_reason"] = "complete"

    return summary


@router.post("/api/ops/outbound/accounts_add_csv")
def accounts_add_csv(
    company_name: str,
    website_domain: str,
    website_url: str | None = None,
    city: str | None = None,
    state: str | None = None,
    source: str = "manual",
    gbp_url: str | None = None,
    notes: str | None = None,
    ok=Depends(require_ops),
):
    """
    Add a single account to the master CSV.
    """
    _ensure_master_csv()
    rows = _read_accounts()
    
    # Check for duplicate
    dom = _normalize_domain(website_domain)
    for r in rows:
        if _normalize_domain(r.get("website_domain", "")) == dom:
            return {"ok": False, "reason": "duplicate_domain"}
    
    # Add new row
    rows.append({
        "company_name": company_name,
        "website_domain": website_domain,
        "website_url": website_url or "",
        "city": city or "",
        "state": state or "",
        "source": source,
        "gbp_url": gbp_url or "",
        "notes": notes or "",
        "status": "new",
        "updated_at": datetime.utcnow().isoformat(),
    })
    
    _write_accounts(rows)
    return {"ok": True, "total_accounts": len(rows)}


@router.get("/api/ops/outbound/accounts_csv_stats")
def accounts_csv_stats(ok=Depends(require_ops)):
    """
    Get stats from the accounts CSV.
    """
    rows = _read_accounts()
    
    status_counts = {}
    for r in rows:
        status = r.get("status", "new")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total": len(rows),
        "status_counts": status_counts,
        "master_csv": MASTER_CSV,
    }
