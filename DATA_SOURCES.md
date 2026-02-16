# TensorMarketData - Data Sources Strategy

## Current Status
- Platform deployed ✅
- No live data yet ❌

## Data Source Options

### Option 1: Free / Cheap (Immediate)
| Source | Cost | Data Type |
|--------|------|-----------|
| SEC EDGAR | Free | Company filings, financials |
| US Census Bureau | Free | Business demographics |
| OpenCorporates | Free | Company registry data |
| Wikipedia Companies | Free | Basic company info |

**Time to implement:** 1-2 days
**Cost:** $0

### Option 2: API Subscriptions (This Week)
| Source | Cost | Data Type |
|--------|------|-----------|
| API Ninjas | $30/mo | Business data, 10k calls |
| Clearbit | $199/mo (est) | Company enrichment |
| Apollo.io | $49/mo | B2B contacts, 10k/mo |
| Bright Data | ~$100+/mo | Web data, proxies |

**Time to implement:** 2-5 days
**Cost:** $30-200/mo

### Option 3: Partnerships
- Partner with data providers
- They provide data, we provide distribution
- Revenue share model

## Recommended Path (MVP)

1. **Start with SEC EDGAR** (Free)
   - Company financials, filings
   - Easy to integrate
   - Shows "real data" works

2. **Add OpenCorporates** (Free)
   - Company registry data
   - Verify company existence

3. **Graduate to paid API**
   - Once we have first customer
   - Based on what they need

## Action Items

- [ ] Integrate SEC EDGAR API (free)
- [ ] Create sample dataset (50 companies)
- [ ] Test search endpoint with real data
- [ ] Show working demo to potential customers
- [ ] Iterate based on feedback

## Budget Request
- $0 for Phase 1 (free sources)
- $50-100/mo for Phase 2 (paid API)
