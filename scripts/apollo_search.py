#!/usr/bin/env python3
"""
Apollo Lead Search Workflow
Uses your existing Apollo subscription to find and enrich leads
"""

import os
import json
import urllib.request
import urllib.parse

API_KEY = "kw_KuGhJAIw3DNrCyHdQSQ"  # Your Apollo key

def search_organizations(query, employee_range="10,100", per_page=10):
    """Search for companies/organizations"""
    url = "https://api.apollo.io/api/v1/organizations/search"
    data = {
        "query": query,
        "employee_count_ranges": employee_range,
        "per_page": per_page
    }
    return _apollo_request(url, data)

def search_people(keywords=None, titles=None, per_page=10):
    """Search for people (decision makers)"""
    url = "https://api.apollo.io/api/v1/mixed_people/api_search"
    data = {"per_page": per_page}
    
    if keywords:
        data["person_keywords"] = keywords
    if titles:
        data["title"] = titles
    
    return _apollo_request(url, data)

def enrich_person(email):
    """Enrich a person by email"""
    url = "https://api.apollo.io/api/v1/enrich_person"
    data = {"email": email}
    return _apollo_request(url, data)

def enrich_company(domain):
    """Enrich a company by domain"""
    url = "https://api.apollo.io/api/v1/enrich_company"
    data = {"domain": domain}
    return _apollo_request(url, data)

def _apollo_request(url, data):
    """Make request to Apollo API"""
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

# Example usage
if __name__ == "__main__":
    import sys
    
    # Example 1: Find AI companies
    print("=== Searching for AI companies ===")
    result = search_organizations("artificial intelligence", per_page=5)
    print(f"Found {result.get('total_entries', 0)} companies")
    for org in result.get('organizations', [])[:5]:
        print(f"  - {org.get('name')} ({org.get('estimated_num_employees')} employees)")
    
    print("\n=== Searching for CEOs at AI companies ===")
    result = search_people(keywords="AI", titles=["CEO", "CTO", "VP Engineering"], per_page=5)
    print(f"Found {result.get('total_entries', 0)} people")
    for person in result.get('people', [])[:5]:
        org = person.get('organization', {})
        print(f"  - {person.get('first_name')} {person.get('last_name_obfuscated')}")
        print(f"    {person.get('title')} at {org.get('name')}")
