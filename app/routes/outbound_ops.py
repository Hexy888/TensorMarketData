# Outbound Operations API Routes

import os
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlmodel import Session
from app.db import get_session
from app.services.outbound_repo_sql import OutboundRepoSQLModel
from app.services.outbound_pipeline import OutboundPipeline
from app.services.account_builder import AccountBuilder

OPS_TOKEN = os.getenv("OPS_TOKEN", "")

router = APIRouter()


def get_repo(session: Session = Depends(get_session)) -> OutboundRepoSQLModel:
    return OutboundRepoSQLModel(session)


def require_ops(x_ops_token: str = Header(default="")):
    if not OPS_TOKEN:
        raise HTTPException(500, "OPS_TOKEN not set")
    if x_ops_token != OPS_TOKEN:
        raise HTTPException(401, "bad ops token")
    return True


@router.post("/api/ops/outbound/apollo_search_enrich")
def apollo_search_enrich(
    company_name: str | None = Query(None),
    domain: str | None = Query(None),
    limit: int = Query(25),
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    1) Apollo search shells (no credits) via people_search_api
    2) Enrich within ENRICH_CAP_DAILY and insert targets (bulk)
    """
    repo = get_repo(session)
    pipe = OutboundPipeline(repo=repo)
    
    shells = pipe.apollo_search_shells(company_name=company_name, domain=domain, limit=limit)
    result = pipe.enrich_and_insert_daily(shells)
    
    return {"ok": True, "shells": len(shells), "result": result}


@router.post("/api/ops/outbound/draft")
def outbound_draft(
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Draft email copy for newly inserted targets (status=new).
    """
    repo = get_repo(session)
    pipe = OutboundPipeline(repo=repo)
    
    targets = repo.fetch_new_targets(limit=200)
    return pipe.draft_copy_for_queued(targets)


@router.post("/api/ops/outbound/send")
def outbound_send(
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Send queued emails within SEND_CAP_DAILY.
    """
    repo = get_repo(session)
    pipe = OutboundPipeline(repo=repo)
    
    return pipe.send_daily_cap()


@router.post("/api/ops/outbound/optout")
def outbound_optout(
    email_or_domain: str = Query(...),
    reason: str = Query("manual"),
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Manual opt-out insertion.
    """
    repo = get_repo(session)
    repo.add_optout(email_or_domain=email_or_domain.strip().lower(), reason=reason)
    return {"ok": True}


@router.get("/api/ops/outbound/stats")
def outbound_stats(
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Get outbound pipeline stats.
    """
    from app.models.outbound import OutboundTarget, OutboundEvent
    
    repo = get_repo(session)
    
    # Count by status
    statuses = session.exec(
        select(OutboundTarget.status, func.count(OutboundTarget.id))
        .group_by(OutboundTarget.status)
    ).all()
    
    status_counts = {s: c for s, c in statuses}
    
    # Today's events
    from datetime import datetime
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_events = session.exec(
        select(OutboundEvent.event_type, func.count(OutboundEvent.id))
        .where(OutboundEvent.created_at >= today_start)
        .group_by(OutboundEvent.event_type)
    ).all()
    
    today_counts = {e: c for e, c in today_events}
    
    return {
        "status_counts": status_counts,
        "today_events": today_counts,
        "send_cap": os.getenv("SEND_CAP_DAILY", "20"),
        "enrich_cap": os.getenv("ENRICH_CAP_DAILY", "40"),
    }


@router.post("/api/ops/outbound/accounts_add")
def accounts_add(
    company_name: str = Query(...),
    website_domain: str = Query(...),
    website_url: str | None = Query(None),
    city: str | None = Query(None),
    state: str | None = Query(None),
    source: str = Query("manual"),
    gbp_url: str | None = Query(None),
    notes: str | None = Query(None),
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Add a new HVAC account to the queue.
    """
    builder = AccountBuilder(session)
    target_id = builder.add_account(
        company_name=company_name,
        website_domain=website_domain,
        website_url=website_url,
        city=city,
        state=state,
        source=source,
        gbp_url=gbp_url,
        notes=notes,
    )
    if target_id:
        return {"ok": True, "target_id": target_id}
    return {"ok": False, "reason": "duplicate_domain"}


@router.post("/api/ops/outbound/accounts_process")
def accounts_process(
    limit: int = Query(30),
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Process pending accounts: call Apollo search/enrich for each domain.
    """
    builder = AccountBuilder(session)
    pipe = OutboundPipeline(repo=get_repo(session))
    
    accounts = builder.get_pending_accounts(limit=limit)
    
    processed = 0
    enriched = 0
    inserted = 0
    
    for account in accounts:
        try:
            # Call Apollo search + enrich for this domain
            shells = pipe.apollo_search_shells(
                domain=account.website_domain,
                limit=50
            )
            
            if shells:
                result = pipe.enrich_and_insert_daily(shells)
                enriched += result.get("enriched", 0)
                inserted += result.get("inserted", 0)
            
            # Mark as processed
            builder.mark_processed(account.id)
            processed += 1
            
        except Exception as e:
            builder.mark_skipped(account.id, str(e)[:100])
            continue
    
    return {
        "ok": True,
        "accounts_processed": processed,
        "shells_found": len(shells) if 'shells' in locals() else 0,
        "enriched": enriched,
        "inserted": inserted,
    }


@router.get("/api/ops/outbound/accounts_stats")
def accounts_stats(
    session: Session = Depends(get_session),
    ok=Depends(require_ops),
):
    """
    Get account builder stats.
    """
    builder = AccountBuilder(session)
    counts = builder.count_by_status()
    return {
        "status_counts": counts,
        "target_metro": os.getenv("TARGET_METRO_WEEK", "Dallas-Fort Worth, TX"),
    }
