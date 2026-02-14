"""
Apollo.io Integration for TensorMarketData
Company Enrichment API
"""

import os
from typing import Optional, Dict, Any, List
import httpx

# Apollo API configuration
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "kw_KuGhJAIw3DNrCyHdQSQ")
APOLLO_BASE_URL = "https://api.apollo.io/api/v1"


async def enrich_company(domain: str) -> Optional[Dict[str, Any]]:
    """
    Enrich company data using Apollo Enrichment API.
    
    Args:
        domain: Company domain (e.g., "google.com")
    
    Returns:
        Company data dict or None if not found
    """
    url = f"{APOLLO_BASE_URL}/enrich company"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": APOLLO_API_KEY
    }
    payload = {"domain": domain}
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("company"):
                    return data["company"]
    except Exception as e:
        print(f"Apollo enrich error for {domain}: {e}")
    
    return None


async def search_companies(
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for companies using Apollo Search API.
    
    Args:
        query: Search query (company name, industry, etc.)
        limit: Max results to return
    
    Returns:
        List of company dicts
    """
    url = f"{APOLLO_BASE_URL}/mixed_companies/search"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": APOLLO_API_KEY
    }
    payload = {
        "query": query,
        "page": 1,
        "per_page": limit
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("companies", [])
    except Exception as e:
        print(f"Apollo search error: {e}")
    
    return []


async def get_company_contacts(
    company_id: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Get contacts for a company using Apollo API.
    
    Args:
        company_id: Apollo company ID
        limit: Max results
    
    Returns:
        List of contact dicts
    """
    url = f"{APOLLO_BASE_URL}/mixed_companies/search"
    headers = {
        "Content-Type": "application/json",
        "Api-Key": APOLLO_API_KEY
    }
    payload = {
        "company_ids": [company_id],
        "page": 1,
        "per_page": limit
    }
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("contacts", [])
    except Exception as e:
        print(f"Apollo contacts error: {e}")
    
    return []
