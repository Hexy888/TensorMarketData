# TensorMarketData KPIs

## North Star Metric
**Revenue-Generating API Queries** - Paid queries executed per month

| Category | KPI | Definition | Target | Frequency |
|----------|-----|------------|--------|-----------|
| **Growth** ||||
| | MAU | Monthly Active Users (unique API callers) | 10% MoM | Weekly |
| | New Signups | Account creations (verified email) | 500/month | Daily |
| | API Calls | Total API requests (all types) | 5M/month | Daily |
| **Engagement** ||||
| | DAU/MAU Ratio | Stickiness metric | >30% | Weekly |
| | Queries per User | Avg API calls per active user | 50/month | Weekly |
| | API Key Adoption | % signups with ≥1 API key | 60% | Weekly |
| **Conversion** ||||
| | Signup → API Key | % creating API key within 7 days | 50% | Weekly |
| | API Key → First Query | % making first query within 7 days | 40% | Weekly |
| | Free → Paid | % free users upgrading in 30 days | 5% | Monthly |
| **Revenue** ||||
| | MRR | Monthly Recurring Revenue | 15% MoM | Monthly |
| | ARPU | Average Revenue Per User | $50/month | Monthly |
| | Revenue per Query | Avg revenue per API call | $0.002 | Monthly |
| **Efficiency** ||||
| | CAC | Customer Acquisition Cost | <$200 | Monthly |
| | LTV | Lifetime Value | >$1,000 | Monthly |
| | LTV:CAC Ratio | Unit economics | >5:1 | Monthly |
| | Payback Period | Months to recover CAC | <6 months | Monthly |
| **Retention** ||||
| | Monthly Churn | % users leaving per month | <5% | Monthly |
| | Enterprise Retention | 12-month retention rate | >80% | Quarterly |
| | Logo Retention | Accounts retained (revenue) | >90% | Monthly |

## Tiered Targets by Company Stage

| Stage | MAU Target | MRR Target | CAC Target |
|-------|------------|------------|------------|
| Seed | 1,000 | $10K | $300 |
| Series A | 10,000 | $100K | $200 |
| Series B | 100,000 | $1M | $150 |

## KPI Hierarchy

```
North Star
└── Revenue Queries
    ├── Growth
    │   ├── MAU → New Signups → API Calls
    │   └── DAU/MAU → Queries/User → API Key Adoption
    └── Monetization
        ├── Conversion Funnel
        │   ├── Signup → API Key (50%)
        │   ├── API Key → First Query (40%)
        │   └── Free → Paid (5%)
        └── Revenue Metrics
            ├── MRR → ARPU → Revenue/Query
            └── CAC → LTV → Payback Period
```

## KPI Ownership
- **Growth KPIs**: Growth Lead
- **Revenue KPIs**: CFO/Head of Revenue
- **Product KPIs**: Head of Product
- **Efficiency KPIs**: CEO
