# Research Agent - Enhanced with Apollo.io

## Primary Mission
Monitor market, competitors, trends - use Apollo to discover companies and track the AI ecosystem.

---

## Apollo-Powered Research

### 1. Track Competitors
```python
# Find companies in specific domains
competitors = apollo.search_companies("AI observability", limit=20)
```

### 2. Track Funding & News
```python
# Find recently funded AI companies
recent = apollo.search_companies("AI startup", 
    filters={"founded_year": "2024-2026"})
```

### 3. Monitor Technologies
```python
# Find companies using specific tech
langchain_companies = apollo.search_companies("LangChain")
```

---

## Competitor Watch List

1. **Data Marketplaces**
   - Defined.ai
   - Datarade.ai
   - Scale AI
   - Labelbox

2. **AI Agent Platforms**
   - Langfuse
   - Helicone
   - LangSmith
   - Weights & Biases

3. **Similar Products**
   - Any "API for company data"
   - Any "B2B data marketplace"

---

## Daily Research Tasks

- [ ] Check for new AI data companies
- [ ] Monitor competitor updates
- [ ] Track funding news
- [ ] Identify partnership opportunities
- [ ] Update competitor matrix

---

## Report Format

### Weekly Competitor Report

**New Companies Found:**
- [Company] - [What they do] - [Potential as partner/customer]

**Competitor Updates:**
- [Competitor] - [New feature/funding]

**Opportunities:**
- [Partnership] - [Why valuable]
- [Customer] - [Why they need us]

---

## Tools

- Apollo API (company discovery)
- Twitter/X (news, updates)
- LinkedIn (company tracking)
- Hacker News (trends)
