# Apollo-Outbound Pipeline Service
# Internal use only for TensorMarketData outreach
# DO NOT distribute Apollo data as a product

import os
import json
from datetime import datetime
from sqlmodel import Session, select, or_
from app.models.outbound import OutboundTarget, OutboundEvent, OutboundOptout
from app.tenant_models import HVACAccount
from app.services.apollo_client import (
    apollo_search_people,
    apollo_enrich_person,
    is_relevant_title,
    extract_contact_from_enrich
)

# Configuration
SEND_CAP_DAILY = int(os.getenv("SEND_CAP_DAILY", "20"))
ENRICH_CAP_DAILY = SEND_CAP_DAILY * 2  # Max enriches per day

def search_hvac_accounts(session: Session, metro: str, limit: int = 20) -> list:
    """
    Search Apollo for HVAC businesses in a metro area.
    Stores raw results in HVACAccount table.
    """
    from app.services.apollo_client import RELEVANT_TITLES
    
    # Parse metro
    city = metro.split(",")[0].strip()
    state = metro.split(",")[-1].strip() if "," in metro else ""
    
    # Build search query
    query = f"HVAC {city}"
    if state:
        query += f" {state}"
    
    results = []
    
    # Search for people at HVAC companies
    response = apollo_search_people(
        query=query,
        titles=RELEVANT_TITLES,
        locations=[city, state] if state else [city],
        page=1
    )
    
    if "error" in response:
        print(f"[APOLLO SEARCH ERROR] {response['error']}")
        return results
    
    # Process results
    people = response.get("people", []) or []
    
    for person in people:
        # Skip if no company
        org = person.get("organization", {})
        if not org:
            continue
        
        company_name = org.get("name", "")
        domain = org.get("domain", "")
        
        if not company_name:
            continue
        
        # Check if already exists
        existing = session.exec(
            select(HVACAccount).where(
                HVACAccount.domain == domain,
                HVACAccount.status != "raw"
            )
        ).first()
        
        if existing:
            continue
        
        # Create raw account
        account = HVACAccount(
            company_name=company_name,
            website_url=f"https://{domain}" if domain else None,
            domain=domain,
            city=city,
            state=state,
            apollo_person_id=person.get("id"),
            person_name=f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
            person_title=person.get("title"),
            status="raw",
            source="apollo"
        )
        session.add(account)
        results.append(account)
    
    session.commit()
    return results

def enrich_accounts(session: Session, limit: int = None) -> int:
    """
    Enrich raw HVAC accounts with Apollo.
    Converts to outbound_targets when email is available.
    """
    if limit is None:
        limit = ENRICH_CAP_DAILY
    
    # Get raw accounts
    accounts = session.exec(
        select(HVACAccount).where(HVACAccount.status == "raw").limit(limit)
    ).all()
    
    enriched_count = 0
    converted_count = 0
    
    for account in accounts:
        if not account.apollo_person_id:
            account.status = "skipped"
            session.add(account)
            continue
        
        # Enrich person
        response = apollo_enrich_person(account.apollo_person_id)
        
        if "error" in response:
            print(f"[APOLLO ENRICH ERROR] {response['error']}")
            continue
        
        # Extract contact
        contact = extract_contact_from_enrich(response)
        
        if not contact or not contact.get("email"):
            account.status = "no_email"
            session.add(account)
            continue
        
        # Update account
        account.person_email = contact.get("email")
        account.person_linkedin = contact.get("linkedin_url")
        account.status = "enriched"
        session.add(account)
        enriched_count += 1
        
        # Check opt-outs
        email = contact["email"].lower()
        domain = email.split("@")[1] if "@" in email else ""
        
        optout = session.exec(
            select(OutboundOptout).where(
                or_(
                    OutboundOptout.email_or_domain == email,
                    OutboundOptout.email_or_domain == domain
                )
            )
        ).first()
        
        if optout:
            account.status = "opted_out"
            session.add(account)
            continue
        
        # Convert to outbound target
        target = OutboundTarget(
            company_name=account.company_name,
            website_url=account.website_url,
            location_city=account.city,
            location_state=account.state,
            contact_email=contact["email"],
            contact_role="unknown",  # Would need title analysis
            owner_name=account.person_name,
            source="apollo",
            status="new"
        )
        session.add(target)
        
        # Log enrichment
        log_event(session, target.id, "enriched_from_apollo", {
            "account_id": account.id,
            "person_id": account.apollo_person_id
        })
        
        converted_count += 1
    
    session.commit()
    return {
        "enriched": enriched_count,
        "converted": converted_count
    }

def log_event(session: Session, target_id: int, event_type: str, meta: dict = None):
    session.add(OutboundEvent(
        target_id=target_id,
        event_type=event_type,
        meta=json.dumps(meta or {}),
        created_at=datetime.utcnow()
    ))
    session.commit()

def run_apollo_pipeline(session: Session, metro: str) -> dict:
    """
    Run the full Apollo -> outbound pipeline:
    1. Search for HVAC accounts
    2. Enrich top accounts
    3. Return summary
    """
    # Step 1: Search
    search_results = search_hvac_accounts(session, metro, limit=30)
    
    # Step 2: Enrich
    enrich_result = enrich_accounts(session)
    
    # Step 3: Count queued
    queued = session.exec(
        select(OutboundTarget).where(OutboundTarget.status == "new")
    ).count()
    
    return {
        "metro": metro,
        "searched": len(search_results),
        "enriched": enrich_result.get("enriched", 0),
        "converted_to_targets": enrich_result.get("converted", 0),
        "queued_targets": queued
    }
