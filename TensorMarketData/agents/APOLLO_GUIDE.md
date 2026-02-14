# Apollo.io Expert Guide
## For TensorMarketData AI Agents

### What Apollo Provides (4,000 credits/mo)

**1. Company Enrichment**
- Get company data from domain (employees, revenue, tech stack)
- Endpoint: `POST /api/v1/enrich_company`

**2. People Enrichment**  
- Get contact info from email
- Find people at companies (names, titles, emails)
- Endpoint: `POST /api/v1/enrich_person`

**3. Company Search**
- Search 30M+ companies by industry, size, location
- Filter by: industry, employee count, revenue, tech
- Endpoint: `POST /api/v1/mixed_companies/search`

**4. People Search**
- Search 220M+ contacts by title, company, skills
- Filter by: job title, seniority, department, location
- Endpoint: `POST /api/v1/mixed_persons/search`

**5. Account Management**
- Create/update accounts in Apollo
- Track lead status

**6. Contact Management**
- Create/update contacts
- Bulk import/export

**7. Deals Pipeline**
- Create and track deals
- Update deal stages

**8. Sequences (Email Automation)**
- Find available sequences
- Add contacts to sequences

**9. Tasks**
- Create follow-up tasks
- Bulk task creation

**10. Call Logging**
- Record call outcomes
- Track conversations

---

### How to Use for TensorMarketData

**Lead Generation:**
1. Search companies by: "AI agents", "LLM", "AI startup"
2. Filter: 10-500 employees, recent funding
3. Enrich each company to get contacts
4. Export emails for outreach

**Data Product:**
- Use Apollo data to enrich our API responses
- Cache company/contact data for customers
- Build proprietary database over time

---

### Key Filters for AI Industry

```python
# Find AI agent companies
{
    "query": "artificial intelligence",
    "filters": {
        "employee_count": "10-500",
        "industry": "computer software",
        "founded_year": "2020-2026"
    }
}

# Find decision makers
{
    "query": "",
    "person_filters": {
        "title": ["CEO", "CTO", "VP Engineering", "Head of AI"],
        "seniority": ["executive", "director"]
    }
}
```

---

### Credits Management

- Company enrichment: ~1 credit
- People search: ~1 credit/result
- Email verification: ~0.5 credit
- **Strategy:** Cache everything, only fetch what's needed
