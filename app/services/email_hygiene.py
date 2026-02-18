# Email Hygiene - List cleaning and validation

from __future__ import annotations
import os
import dns.resolver
from typing import Optional

DELIV_FREE_EMAIL_BLOCK = os.getenv("DELIV_FREE_EMAIL_BLOCK", "1") == "1"
DELIV_REQUIRE_MX = os.getenv("DELIV_REQUIRE_MX", "1") == "1"
DELIV_REQUIRE_SITE_DOMAIN = os.getenv("DELIV_REQUIRE_SITE_DOMAIN", "1") == "1"

FREE_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", 
    "aol.com", "icloud.com", "proton.me", "protonmail.com"
}


def recipient_domain(email: str) -> str:
    """Extract domain from email."""
    return (email.split("@", 1)[1].strip().lower()) if "@" in email else ""


def has_mx(domain: str) -> bool:
    """Check if domain has MX records."""
    try:
        dns.resolver.resolve(domain, "MX")
        return True
    except Exception:
        return False


def hygiene_ok(*, email: str, website_domain: str) -> bool:
    """
    Check if recipient passes hygiene gates:
    - Not a free email provider (if DELIV_FREE_EMAIL_BLOCK)
    - Has MX record (if DELIV_REQUIRE_MX)
    - Has website domain (if DELIV_REQUIRE_SITE_DOMAIN)
    """
    dom = recipient_domain(email)
    if not dom:
        return False
    
    if DELIV_FREE_EMAIL_BLOCK and dom in FREE_DOMAINS:
        return False
    
    if DELIV_REQUIRE_SITE_DOMAIN and not (website_domain or "").strip():
        return False
    
    if DELIV_REQUIRE_MX and not has_mx(dom):
        return False
    
    return True
