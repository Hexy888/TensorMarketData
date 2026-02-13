# TensorMarketData API Terms of Use

**Last Updated: February 12, 2026**

## 1. Agreement Overview

These API Terms of Use ("API Terms") govern your access to and use of TensorMarketData's application programming interfaces (APIs), developer tools, SDKs, and documentation (collectively, "APIs"). These terms supplement the main Terms of Service; in case of conflict, these API Terms prevail for API-related matters.

## 2. API Access and Registration

### Getting Started
1. Create a TensorMarketData account
2. Generate API keys in the developer dashboard
3. Review documentation and rate limits
4. Begin integration

### API Keys
- Keep keys secure; never commit to source control
- One key per application is recommended
- Keys can be regenerated in the dashboard
- You're responsible for all activity under your keys

## 3. API Tiers and Limits

| Tier | Rate Limit | Monthly Credits | Features |
|------|------------|-----------------|----------|
| Free | 100 req/min | 10,000 | Basic datasets, community support |
| Developer | 1,000 req/min | 100,000 | Full catalog, email support |
| Business | 10,000 req/min | 1,000,000 | Priority support, analytics |
| Enterprise | Custom | Custom | Dedicated infrastructure, SLA |

### Overage and Rate Limiting
- Requests exceeding limits receive HTTP 429
- Exponential backoff recommended
- Overage billing available for Developer+ tiers

## 4. Permitted Use

### You May:
- Integrate APIs into your applications and AI agents
- Make reasonable requests for your application's functionality
- Cache data as needed for user experience
- Use our APIs for internal business operations

### You Must Not:
- Exceed rate limits or attempt to circumvent them
- Use APIs to build competing products
- Scrape data beyond normal API usage
- Redistribute API access or keys
- Use APIs for illegal, harmful, or abusive purposes

## 5. Data Usage and Licensing

### Data from APIs
- Data retrieved via API is subject to the license specified in the data listing
- Review license terms before use; some data has restrictions
- Attribution may be required; follow guidelines in documentation
- Storage and caching must comply with license terms

### Your Data
- You retain ownership of data you provide to APIs
- You grant us a license to process data as needed to provide services
- Don't send sensitive personal data unless necessary; see Data Processing Agreement

## 6. Developer Responsibilities

### Security
- Implement proper authentication in your applications
- Rotate keys periodically
- Use HTTPS for all API communications
- Report security vulnerabilities immediately

### Compliance
- Ensure your use complies with applicable laws
- Maintain your own legal terms (Privacy Policy, ToS)
- Don't use APIs in ways that violate third-party rights

## 7. TensorMarketData Responsibilities

### Availability
- Target 99.9% uptime for paid tiers (see SLA)
- Provide status updates at status.tensormarketdata.com
- Schedule maintenance with advance notice

### Support
- Documentation: docs.tensormarketdata.com
- Developer community: community.tensormarketdata.com
- Email support based on tier
- Enterprise: Dedicated Slack channel and phone support

## 8. Deprecation and Changes

### Version Support
- We support major versions for 24 months
- Deprecation notices given 90 days in advance
- Migration guides provided for major changes

### Breaking Changes
- Will not be introduced without notice
- Will be communicated via email and developer dashboard
- Legacy support available for enterprise customers

## 9. Fees and Payment

- Free tier available for development/testing
- Pay-as-you-go and subscription options
- Invoices sent monthly; net 30 payment terms
- See pricing page for current rates

## 10. Termination

### Your Right to Terminate
- Stop using APIs at any time
- Delete API keys from your systems
- No refund for prepaid credits

### Our Right to Terminate
- Immediate termination for violation of these terms
- 30 days notice for policy changes
- Suspension for non-payment

### Effects of Termination
- License to use APIs ends
- Outstanding obligations survive
- Data retrieval must occur before termination (if possible)

## 11. Disclaimer and Liability

**APIs PROVIDED "AS IS" WITHOUT WARRANTY.** We don't guarantee error-free or uninterrupted operation.

**LIABILITY LIMITED TO FEES PAID IN PRIOR 12 MONTHS.** We won't be liable for indirect, consequential, or punitive damages.

## 12. Contact

Developer Support: api-support@tensormarketdata.com
Sales: enterprise@tensormarketdata.com

---

*This is a simplified example document. Consult qualified legal counsel before use.*
