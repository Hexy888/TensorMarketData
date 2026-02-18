# Apollo Integration Client - Updated with working endpoints
# Uses: /mixed_people/api_search (search) + /people/match (enrich) + /people/bulk_match (bulk enrich)

import os
import time
import random
import requests
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY", "")
APOLLO_BASE = "https://api.apollo.io/api/v1"


class ApolloError(RuntimeError):
    pass


def _headers() -> Dict[str, str]:
    if not APOLLO_API_KEY:
        raise ApolloError("APOLLO_API_KEY not set")
    return {"Content-Type": "application/json", "X-Api-Key": APOLLO_API_KEY}


def _sleep_backoff(attempt: int) -> None:
    """Exponential backoff + jitter."""
    base = min(2 ** attempt, 16)
    time.sleep(base + random.random())


def _post(url: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """Retry on 429 + transient 5xx."""
    last_err = None
    for attempt in range(0, 5):
        try:
            r = requests.post(url, headers=_headers(), json=payload, timeout=timeout)
            if r.status_code in (429, 500, 502, 503, 504):
                last_err = f"{r.status_code}: {r.text[:300]}"
                _sleep_backoff(attempt)
                continue
            if r.status_code >= 400:
                raise ApolloError(f"POST {url} failed {r.status_code}: {r.text[:500]}")
            return r.json()
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = str(e)
            _sleep_backoff(attempt)
            continue
    raise ApolloError(f"POST {url} failed after retries: {last_err}")


@dataclass
class ApolloPersonShell:
    person_id: str
    first_name: str
    last_name: str
    title: str
    organization_name: str
    organization_domain: Optional[str]
    city: Optional[str]
    state: Optional[str]


@dataclass
class ApolloEnrichedContact:
    person_id: str
    first_name: str
    last_name: str
    title: str
    organization_name: str
    organization_domain: Optional[str]
    email: Optional[str]
    city: Optional[str]
    state: Optional[str]


class ApolloClient:
    """
    Endpoints:
    - Search: POST /mixed_people/api_search (no credits)
    - Enrich 1: POST /people/match (credits)
    - Enrich 10: POST /people/bulk_match (credits)
    """

    # ---------------------------
    # SEARCH (no credits)
    # ---------------------------
    def people_search_api(
        self,
        *,
        q_organization_name: Optional[str] = None,
        q_organization_domains: Optional[List[str]] = None,
        person_titles: Optional[List[str]] = None,
        per_page: int = 10,
        page: int = 1,
    ) -> List[ApolloPersonShell]:
        url = f"{APOLLO_BASE}/mixed_people/api_search"
        payload: Dict[str, Any] = {"page": page, "per_page": min(max(per_page, 1), 50)}
        
        if q_organization_name:
            payload["q_organization_name"] = q_organization_name
        if q_organization_domains:
            payload["q_organization_domains"] = q_organization_domains
        if person_titles:
            payload["person_titles"] = person_titles

        data = _post(url, payload)
        
        people = data.get("people") or data.get("contacts") or []
        out: List[ApolloPersonShell] = []
        
        for p in people:
            person_id = str(p.get("person_id") or p.get("id") or "").strip()
            if not person_id:
                continue
            
            org = p.get("organization") or {}
            org_name = org.get("name") or p.get("organization_name") or ""
            org_domain = (
                org.get("primary_domain") or 
                org.get("website_url") or 
                p.get("organization_domain") or 
                p.get("domain")
            )
            
            out.append(
                ApolloPersonShell(
                    person_id=person_id,
                    first_name=p.get("first_name") or "",
                    last_name=p.get("last_name") or "",
                    title=p.get("title") or "",
                    organization_name=org_name,
                    organization_domain=org_domain,
                    city=p.get("city"),
                    state=p.get("state"),
                )
            )
        return out

    # ---------------------------
    # ENRICH (credits) - single
    # ---------------------------
    def people_match(
        self,
        *,
        person_id: Optional[str] = None,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        organization_name: Optional[str] = None,
    ) -> ApolloEnrichedContact:
        """Use the most specific identifiers you have."""
        url = f"{APOLLO_BASE}/people/match"
        payload: Dict[str, Any] = {}
        
        if person_id:
            payload["person_id"] = person_id
        if email:
            payload["email"] = email
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name
        if domain:
            payload["domain"] = domain
        if organization_name:
            payload["organization_name"] = organization_name

        if not payload:
            raise ApolloError("people_match requires person_id OR identifying fields")

        data = _post(url, payload)
        
        p = data.get("person") or data.get("contact") or data
        org = p.get("organization") or {}
        
        pid = str(p.get("person_id") or p.get("id") or person_id or "").strip()
        if not pid:
            raise ApolloError("people_match returned no person_id")

        org_name = org.get("name") or p.get("organization_name") or (organization_name or "")
        org_domain = org.get("primary_domain") or org.get("website_url") or domain

        return ApolloEnrichedContact(
            person_id=pid,
            first_name=p.get("first_name") or (first_name or ""),
            last_name=p.get("last_name") or (last_name or ""),
            title=p.get("title") or "",
            organization_name=org_name,
            organization_domain=org_domain,
            email=p.get("email"),
            city=p.get("city"),
            state=p.get("state"),
        )

    # ---------------------------
    # ENRICH (credits) - bulk up to 10
    # ---------------------------
    def people_bulk_match(self, matches: List[Dict[str, Any]]) -> List[ApolloEnrichedContact]:
        """matches: list of up to 10 dicts with person_id."""
        if not matches:
            return []
        if len(matches) > 10:
            raise ApolloError("people_bulk_match supports up to 10 per call")

        url = f"{APOLLO_BASE}/people/bulk_match"
        payload = {"people": matches}
        
        data = _post(url, payload)
        
        people = data.get("people") or data.get("contacts") or []
        out: List[ApolloEnrichedContact] = []
        
        for p in people:
            org = p.get("organization") or {}
            pid = str(p.get("person_id") or p.get("id") or "").strip()
            if not pid:
                continue

            out.append(
                ApolloEnrichedContact(
                    person_id=pid,
                    first_name=p.get("first_name") or "",
                    last_name=p.get("last_name") or "",
                    title=p.get("title") or "",
                    organization_name=org.get("name") or p.get("organization_name") or "",
                    organization_domain=org.get("primary_domain") or org.get("website_url") or p.get("domain"),
                    email=p.get("email"),
                    city=p.get("city"),
                    state=p.get("state"),
                )
            )
        return out


# Title filters for HVAC targeting
TITLE_FILTERS = [
    "Owner", "President", "Founder", "General Manager",
    "Office Manager", "Operations Manager", "Service Manager"
]
