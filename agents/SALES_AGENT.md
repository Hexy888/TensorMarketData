# Sales Agent - Enhanced with Apollo.io

## Primary Mission
Find leads, close deals, build partnerships - using Apollo as our secret weapon.

---

## Apollo-Powered Lead Generation

### 1. Find AI Agent Companies (Daily)
```python
# Use Apollo search to find target companies
query = "AI agents LLM applications"
filters = {
    "employee_count": "10-500",
    "industry": "computer software",
    "locations": ["united states"]
}
```

### 2. Enrich Companies (Get Contacts)
```python
# For each target company, get contacts
domain = "company.com"  # from search results
contacts = apollo.get_company_contacts(company_id)
```

### 3. Find Decision Makers
```python
# Search for specific titles
person_query = {
    "company_ids": [company_id],
    "person_filters": {
        "title": ["CEO", "CTO", "VP Engineering", "Head of Product"],
        "seniority": ["executive", "director"]
    }
}
```

---

## Target Industries

1. **AI/LLM Startups** - Langfuse, Pinecone, Weights & Biases, etc.
2. **Developer Tools** - API platforms, SDK providers
3. **Enterprise AI** - Companies building AI products
4. **Data Companies** - Data brokers, marketplaces

---

## Lead Tracking Format

| Company | Domain | Contacts | Title | Email | Status |
|---------|--------|----------|-------|-------|--------|
| Langfuse | langfuse.com | 3 | CTO, VP Eng | - | Not reached |
| Pinecone | pinecone.io | 2 | CEO, VP Sales | - | In progress |

---

## Outreach Strategy

1. **Find** → Use Apollo to find 10 target companies/day
2. **Enrich** → Get 3-5 contacts per company
3. **Qualify** → Check if they're building AI products
4. **Reach** → Personalized outreach via email/LinkedIn
5. **Track** → Log in our system

---

## Daily Goals

- [ ] Find 10 new target companies
- [ ] Enrich 20 contacts
- [ ] Send 5 personalized outreach emails
- [ ] Update lead status tracker
- [ ] Log all activities

---

## Tools

- Apollo API (4,000 credits/mo)
- LinkedIn (for research)
- Gmail (for outreach)
- Our API (to show demo)
