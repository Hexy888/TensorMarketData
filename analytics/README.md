# TensorMarketData Analytics - README

## Quick Start

This analytics setup is designed to track all key metrics for TensorMarketData's B2B data marketplace.

## Directory Structure

```
analytics/
├── dashboards/
│   ├── plausible-config.yaml      # Web analytics config
│   ├── mixpanel-config.yaml       # Product analytics config
│   ├── mixpanel-jql.yaml          # Custom JQL queries
│   └── metabase-config.yaml       # Dashboard configurations
├── conversions/
│   └── funnel-tracking.yaml       # Conversion funnel setup
├── alerts/
│   └── alerting-config.yaml       # Alert thresholds & channels
├── reports/
│   └── automated-reports.yaml     # Daily/weekly/monthly reports
└── docs/
    ├── ARCHITECTURE.md            # System architecture
    ├── KPIS.md                    # KPI definitions & targets
    ├── TARGETS.md                 # Quarterly OKRs & targets
    └── GLOSSARY.md                # Metrics glossary
```

## Key Metrics to Track

| Category | Key Metrics |
|----------|-------------|
| **Growth** | MAU, New Signups, API Calls |
| **Engagement** | DAU/MAU, Queries/User, API Key Adoption |
| **Conversion** | Signup→API Key→Query→Paid funnel |
| **Revenue** | MRR, ARPU, Revenue/Query |
| **Efficiency** | CAC, LTV, LTV:CAC, Payback Period |
| **Retention** | Monthly Churn, NRR, Logo Retention |

## Getting Started

1. **Set up Plausible** for website analytics
2. **Configure Mixpanel** for product tracking
3. **Create Metabase** dashboards using the provided configs
4. **Set up alerts** in PagerDuty/Slack
5. **Schedule automated reports**

## Contact

- Analytics issues: #analytics Slack channel
- Data requests: data-team@tensormarketdata.com
- Dashboard access: Metabase admin
