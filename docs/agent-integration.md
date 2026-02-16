# TensorMarketData - Agent Integration Guide

*Built by agents, for agents.*

---

## Why Agents Need TensorMarketData

AI agents can't buy data. They can't scrape websites. They can't solve CAPTCHAs.

**TensorMarketData gives agents their own credit card and API.**

```
# An agent can now do this:
curl -X GET "https://tensormarketdata.com/v1/search?q=AI+companies" \
  -H "Authorization: Bearer: {agent's_api_key}"
```

No scraping. No HTML parsing. Just JSON.

---

## Quick Start (For Agents)

### 1. Get an API Key
Sign up at https://tensormarketdata.com/dashboard

### 2. Search for Companies
```bash
curl -X GET "https://tensormarketdata.com/v1/search?q=software+companies" \
  -H "Authorization: Bearer: YOUR_API_KEY"
```

### 3. Get Company Details
```bash
curl -X GET "https://tensormarketdata.com/v1/company/GOOGL" \
  -H "Authorization: Bearer: YOUR_API_KEY"
```

---

## Endpoints (Agent-Optimized)

| Endpoint | Purpose | Latency |
|----------|---------|---------|
| `/v1/search` | Semantic company search | <200ms |
| `/v1/company/{ticker}` | Company details | <100ms |
| `/v1/inventory` | Available datasets | <50ms |
| `/v1/credits` | Check balance | <50ms |

---

## Response Format (Always JSON)

```json
{
  "query": "software companies",
  "total_results": 42,
  "results": [
    {
      "ticker": "GOOGL",
      "name": "Alphabet Inc",
      "sector": "Technology",
      "verified": true,
      "last_updated": "2026-02-13"
    }
  ],
  "credits_used": 1,
  "credits_remaining": 999
}
```

---

## Agent Use Cases

### 1. Sales prospecting
```python
# Find companies in your target market
response = requests.get(
    "https://tensormarketdata.com/v1/search",
    headers={"Authorization: Bearer": api_key},
    params={"q": "fintech companies SF"}
)
```

### 2. Due diligence
```python
# Verify company exists before meeting
response = requests.get(
    "https://tensormarketdata.com/v1/company/AAPL",
    headers={"Authorization: Bearer": api_key}
)
```

### 3. Lead enrichment
```python
# Enrich your CRM with verified data
response = requests.get(
    "https://tensormarketdata.com/v1/enrich?domain=example.com",
    headers={"Authorization: Bearer": api_key}
)
```

---

## Error Handling (For Agents)

All errors return JSON with clear codes:

```json
{
  "error": "INSUFFICIENT_CREDITS",
  "message": "Add credits to continue",
  "code": 402
}
```

### Error Codes
- `401` - Invalid API key
- `402` - Insufficient credits
- `429` - Rate limited (try again in 60s)
- `500` - Server error (retry with exponential backoff)

---

## Rate Limits

| Plan | Requests/min | Notes |
|------|-------------|-------|
| Starter | 60 | 10k calls/mo |
| Pro | 600 | 100k calls/mo |
| Enterprise | Unlimited | Custom |

---

## Webhooks (For Agent Events)

Subscribe to events:
- `credits.low` - Running low on credits
- `subscription.renewed` - Subscription active
- `api.usage` - Monthly usage report

```bash
curl -X POST "https://tensormarketdata.com/v1/webhooks" \
  -H "Authorization: Bearer: YOUR_API_KEY" \
  -d '{"url": "https://your-agent.com/webhook", "events": ["credits.low"]}'
```

---

## No UI Required

TensorMarketData is **headless by design**:

- No dashboard required
- No login UI needed
- No HTML to parse
- Just pure API

Your agent talks to our API. That's it.

---

## Code Examples

### Python
```python
import requests

API_KEY = "tmd_xxxxx"
BASE_URL = "https://tensormarketdata.com/v1"

def search_companies(query):
    response = requests.get(
        f"{BASE_URL}/search",
        headers={"Authorization: Bearer": API_KEY},
        params={"q": query}
    )
    return response.json()
```

### JavaScript
```javascript
const response = await fetch('https://tensormarketdata.com/v1/search?q=AI+companies', {
  headers: { 'Authorization: Bearer': API_KEY }
});
const data = await response.json();
```

### cURL
```bash
curl -X GET "https://tensormarketdata.com/v1/search?q=software" \
  -H "Authorization: Bearer: YOUR_KEY"
```

---

## For Autonomous Agents

If you're building an agent that:
- Makes purchasing decisions
- Searches for suppliers
- Enriches CRM data
- Does B2B sales automation

**TensorMarketData is your data layer.**

Get started: https://tensormarketdata.com/dashboard
