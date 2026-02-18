# HVAC Account Builder Service
# Generates account lists from domains → feeds to Apollo outbound pipeline

import os
import csv
import re
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, func
from app.models.outbound import OutboundTarget


# Configuration
TARGET_METRO_WEEK = os.getenv("TARGET_METRO_WEEK", "Dallas-Fort Worth, TX")
HVAC_KEYWORDS = ["hvac", "air conditioning", "ac repair", "heating contractor", "furnace repair"]
RESULT_CAP_DAILY = 30  # Gather 30 accounts/day


def normalize_domain(domain_or_url: str | None) -> Optional[str]:
    """Remove protocol, www, path to get root domain."""
    if not domain_or_url:
        return None
    
    d = domain_or_url.strip().lower()
    d = d.replace("https://", "").replace("http://", "")
    d = d.replace("www.", "")
    d = d.split("/")[0]
    d = d.split(":")[0]
    return d if d else None


def is_hvac_company(company_name: str) -> bool:
    """Check if company name suggests HVAC business."""
    name_lower = company_name.lower()
    for keyword in HVAC_KEYWORDS:
        if keyword in name_lower:
            return True
    return False


def extract_city_state(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract city, state from text (footer, contact page, etc)."""
    # Simple pattern: "City, ST" or "City State"
    match = re.search(r'([A-Za-z\s]+),\s*([A-Z]{2})', text)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    
    # Try 2-letter state code pattern
    match = re.search(r'\b([A-Z]{2})\s+\d{5}', text)
    if match:
        return None, match.group(1)
    
    return None, None


class AccountBuilder:
    """Build HVAC account list from domains."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def add_account(
        self,
        company_name: str,
        website_domain: str,
        website_url: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        source: str = "manual",
        gbp_url: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[int]:
        """Add account if not duplicate. Returns ID or None if skipped."""
        domain = normalize_domain(website_domain)
        if not domain:
            return None
        
        # Check if domain already exists
        existing = self.session.exec(
            select(OutboundTarget).where(OutboundTarget.website_domain == domain)
        ).first()
        
        if existing:
            return None
        
        # Check if HVAC (skip if not clearly HVAC)
        if not is_hvac_company(company_name):
            # Could add to a separate table for review
            pass
        
        # Store in OutboundTarget with status="account" (special status)
        target = OutboundTarget(
            company_name=company_name.strip(),
            website_domain=domain,
            website_url=website_url,
            location_city=city,
            location_state=state,
            contact_email="",  # Will be filled by Apollo enrich
            contact_role="unknown",
            source=source,
            notes=notes or "",
            status="account",  # Special status: waiting for Apollo
        )
        self.session.add(target)
        self.session.commit()
        self.session.refresh(target)
        return target.id
    
    def get_pending_accounts(self, limit: int = 30) -> list:
        """Get accounts waiting for Apollo enrichment."""
        return self.session.exec(
            select(OutboundTarget)
            .where(OutboundTarget.status == "account")
            .order_by(OutboundTarget.created_at.asc())
            .limit(limit)
        ).all()
    
    def mark_processed(self, target_id: int) -> None:
        """Mark account as processed."""
        target = self.session.get(OutboundTarget, target_id)
        if target:
            target.status = "new"  # Ready for outbound pipeline
            self.session.add(target)
            self.session.commit()
    
    def mark_skipped(self, target_id: int, reason: str) -> None:
        """Mark account as skipped."""
        target = self.session.get(OutboundTarget, target_id)
        if target:
            target.notes = f"{target.notes}; SKIPPED: {reason}" if target.notes else f"SKIPPED: {reason}"
            target.status = "skipped"
            self.session.add(target)
            self.session.commit()
    
    def count_by_status(self) -> dict:
        """Count accounts by status."""
        statuses = self.session.exec(
            select(OutboundTarget.status, func.count(OutboundTarget.id))
            .where(OutboundTarget.source.in_(["manual", "directory", "serp"]))
            .group_by(OutboundTarget.status)
        ).all()
        return {s: c for s, c in statuses}


# CSV file helpers
ACCOUNTS_DIR = "/Users/hexbornestudio/.openclaw/workspace/TensorMarketData-v2/data/accounts"


def load_accounts_from_csv(filepath: str) -> list:
    """Load accounts from CSV file."""
    accounts = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                accounts.append(row)
    except FileNotFoundError:
        pass
    return accounts


def save_accounts_to_csv(accounts: list, filepath: str) -> None:
    """Save accounts to CSV file."""
    if not accounts:
        return
    
    fieldnames = ["company_name", "website_domain", "website_url", "city", "state", "source", "gbp_url", "notes", "status"]
    
    with open(filepath, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(accounts)
