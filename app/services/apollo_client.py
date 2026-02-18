# Apollo Integration Service
# Internal use only for TensorMarketData outreach
# DO NOT distribute Apollo data as a product

import os
import requests
from typing import Optional

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"

def apollo_search_people(query: str, titles: list = None, locations: list = None, page: int = 1) -> dict:
    """
    Search for people using Apollo People API.
    Uses mixed_people endpoint for search.
    """
    if not APOLLO_API_KEY:
        return {"error": "APOLLO_API_KEY not set"}
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    
    payload = {
        "api_key": APOLLO_API_KEY,
        "q": query,
        "page": page,
        "per_page": 10
    }
    
    if titles:
        payload["titles"] = titles
    
    if locations:
        payload["locations"] = locations
    
    try:
        response = requests.post(
            f"{APOLLO_BASE_URL}/mixed_people/search",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def apollo_enrich_person(person_id: str) -> dict:
    """
    Enrich a person using Apollo People Enrichment API.
    Returns verified email if available.
    """
    if not APOLLO_API_KEY:
        return {"error": "APOLLO_API_KEY not set"}
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    
    payload = {
        "api_key": APOLLO_API_KEY,
        "id": person_id
    }
    
    try:
        response = requests.post(
            f"{APOLLO_BASE_URL}/people/enrich",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def apollo_get_company(domain: str) -> dict:
    """
    Get company info using Apollo Company Enrichment API.
    """
    if not APOLLO_API_KEY:
        return {"error": "APOLLO_API_KEY not set"}
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache"
    }
    
    payload = {
        "api_key": APOLLO_API_KEY,
        "domain": domain
    }
    
    try:
        response = requests.post(
            f"{APOLLO_BASE_URL}/companies/enrich",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Title filters for HVAC targeting
RELEVANT_TITLES = [
    "owner",
    "president", 
    "founder",
    "general manager",
    "office manager",
    "operations manager",
    "service manager",
    "hvac manager"
]

# Exclude titles
EXCLUDED_TITLES = [
    "student",
    "intern",
    "assistant",
    "associate"
]

def is_relevant_title(title: str) -> bool:
    """Check if a title is relevant for outreach."""
    if not title:
        return False
    
    title_lower = title.lower()
    
    # Exclude clearly irrelevant
    for excluded in EXCLUDED_TITLES:
        if excluded in title_lower:
            return False
    
    # Check relevant
    for relevant in RELEVANT_TITLES:
        if relevant in title_lower:
            return True
    
    return False

def extract_contact_from_enrich(data: dict) -> Optional[dict]:
    """
    Extract clean contact info from Apollo enrichment response.
    """
    if not data.get("person"):
        return None
    
    person = data["person"]
    
    # Get verified email
    email = person.get("email")
    if not email:
        # Try alternate email fields
        email = person.get("confirmed_work_email") or person.get("personal_email")
    
    # Skip if no email or personal free email
    if not email:
        return None
    
    # Check for free email domains
    free_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
    email_domain = email.split("@")[1].lower() if "@" in email else ""
    if email_domain in free_domains:
        # Could still use if clearly business-related
        pass  # Accept but prefer work email
    
    return {
        "email": email,
        "first_name": person.get("first_name", ""),
        "last_name": person.get("last_name", ""),
        "title": person.get("title", ""),
        "linkedin_url": person.get("linkedin_url", ""),
        "phone": person.get("phone_number", ""),
        "company": person.get("organization", {}).get("name", ""),
        "company_domain": person.get("organization", {}).get("domain", "")
    }
