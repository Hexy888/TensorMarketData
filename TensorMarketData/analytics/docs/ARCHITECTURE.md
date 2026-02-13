# TensorMarketData Analytics Architecture

## Overview
Analytics infrastructure for measuring B2B data marketplace performance and growth.

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Analytics | Plausible | Privacy-focused website/app analytics |
| Product Analytics | Mixpanel | User behavior, funnels, retention |
| Business Metrics | Custom SQL queries | CAC, LTV, revenue, churn |
| Alerting | PagerDuty + Slack | Anomaly detection |
| Visualization | Metabase + Looker | Self-service dashboards |
| Data Pipeline | BigQuery + dbt | Data warehouse & transformations |

## Data Flow

```
User Actions → Plausible/Mixpanel → BigQuery → dbt Transformations → Metabase Dashboards
                    ↓                    ↓                    ↓
              Real-time events    Raw events         Business metrics
                                        ↓
                                   Alerting system
```

## Key Data Streams

1. **Website Traffic** (Plausible)
   - Page views, sessions, referrers
   - UTM parameters for campaign tracking

2. **Product Usage** (Mixpanel)
   - Signup flow completion
   - API key generation
   - Query patterns
   - Feature adoption

3. **Revenue** (Stripe + Custom)
   - Subscriptions, usage-based billing
   - Enterprise contracts

4. **Support** (Intercom)
   - Ticket volume, resolution time
   - NPS scores

## Environment Configuration

```yaml
analytics:
  platforms:
    plausible:
      site_id: tensormarketdata.com
      api_key: ${PLAUSIBLE_API_KEY}
    mixpanel:
      project_token: ${MIXPANEL_PROJECT_TOKEN}
      api_secret: ${MIXPANEL_API_SECRET}
    bigquery:
      dataset: tensormarketdata_prod
      location: US
```

## Privacy Compliance
- GDPR compliant (EU data residency optional)
- No personal data stored in analytics
- Data retention: 24 months for analysis, 7 years for compliance
