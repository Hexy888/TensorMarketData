# TensorMarketData Data Sources Documentation

## Overview
TensorMarketData aggregates supplier data from multiple sources for AI agent consumption.

## Data Sources

### 1. Government Databases

#### SEC EDGAR (sec_edgar)
- **URL**: https://www.sec.gov/edgar
- **Data Type**: Company filings, financial data, executive info
- **Update Frequency**: Daily
- **API**: Yes (https://data.sec.gov)
- **Compliance**: Public domain
- **Quality Score**: High (official regulatory filings)
- **Fields**: CIK, company name, filings, financials, addresses
- **Rate Limits**: None for API

#### FDA Establishment Registration (fda)
- **URL**: https://api.fda.gov
- **Data Type**: Medical device/pharma company registrations
- **Update Frequency**: Weekly
- **API**: Yes
- **Compliance**: Public health data
- **Quality Score**: High (regulated entities)
- **Fields**: Establishment ID, name, address, product categories

#### SAM.gov Contractors (gov_contracts)
- **URL**: https://sam.gov
- **Data Type**: Government contractor registry
- **Update Frequency**: Daily
- **API**: Yes (sam.gov API)
- **Compliance**: Federal contracting data
- **Quality Score**: High (verified contractors)
- **Fields**: CAGE code, DUNS, NAICS codes, capabilities

### 2. Business Directories

#### Better Business Bureau (bbb)
- **URL**: https://www.bbb.org
- **Data Type**: Business ratings, complaints, accreditation
- **Update Frequency**: Daily
- **API**: Limited
- **Compliance**: Terms of service apply
- **Quality Score**: Medium-High (verified complaints)
- **Fields**: Rating, accreditation, complaint count, address

#### Yellow Pages (yellowpages)
- **URL**: https://www.yellowpages.com
- **Data Type**: Business listings, contact info
- **Update Frequency**: Continuous
- **API**: No (scraping)
- **Compliance**: robots.txt compliant
- **Quality Score**: Medium (user-submitted)
- **Fields**: Name, phone, address, category, hours

#### Manta (manta)
- **URL**: https://www.manta.com
- **Data Type**: Small business directory
- **Update Frequency**: Weekly
- **API**: No (scraping)
- **Compliance**: robots.txt compliant
- **Quality Score**: Medium (SMB focus)
- **Fields**: Name, location, employee count, industry

#### OpenCorporates (opencorporates)
- **URL**: https://opencorporates.com
- **Data Type**: Global company registry aggregation
- **Update Frequency**: Daily
- **API**: Yes (requires registration)
- **Compliance**: Varies by jurisdiction
- **Quality Score**: High (official filings)
- **Fields**: Company number, jurisdiction, officers, filings

### 3. Company Data APIs

#### Crunchbase (crunchbase)
- **URL**: https://www.crunchbase.com
- **Data Type**: Company profiles, funding, acquisitions
- **Update Frequency**: Daily
- **API**: Yes (paid)
- **Compliance**: Terms of service
- **Quality Score**: High (verified data)
- **Fields**: Funding, investors, leadership, competitors

#### LinkedIn Sales Navigator (linkedin_sales)
- **URL**: https://www.linkedin.com
- **Data Type**: Professional profiles, company info
- **Update Frequency**: Real-time
- **API**: Yes (premium)
- **Compliance**: LinkedIn API terms
- **Quality Score**: High (verified professionals)
- **Fields**: Employees, job titles, company size, industry

### 4. Industry Associations

#### Technology (tech)
- **Sources**: TechAmerica, ITI
- **Data Type**: Tech company directories
- **Quality Score**: High (verified members)

#### Healthcare (healthcare)
- **Sources**: AdvaMED, PhRMA
- **Data Type**: Medical device/pharma directories
- **Quality Score**: High (regulated industry)

#### Manufacturing (manufacturing)
- **Sources**: NAM, MAPI
- **Data Type**: Manufacturing company directories
- **Quality Score**: Medium-High (member verified)

#### Finance (finance)
- **Sources**: SIFMA, ABA
- **Data Type**: Financial services directories
- **Quality Score**: High (regulated industry)

## Quality Scores

### Score Calculation
Data quality scores are calculated on a 0-1 scale based on:

| Dimension | Weight | Description |
|-----------|--------|------------|
| Completeness | 25% | Percentage of required fields filled |
| Accuracy | 25% | Validation of email, phone, format |
| Consistency | 15% | Internal data consistency checks |
| Timeliness | 10% | Data freshness based on scrape date |
| Validity | 15% | Format compliance |
| Uniqueness | 10% | Duplicate detection |

### Score Thresholds

| Score Range | Rating | Action |
|-------------|--------|--------|
| 0.8 - 1.0 | Excellent | Ready for use |
| 0.6 - 0.79 | Good | Minor enrichment needed |
| 0.4 - 0.59 | Fair | Significant enrichment needed |
| 0.0 - 0.39 | Poor | Consider removal |

## Data Freshness

| Source | Update Frequency | Retention Policy |
|--------|------------------|------------------|
| SEC EDGAR | Daily | Indefinite |
| FDA | Weekly | 7 years |
| SAM.gov | Daily | Active + 2 years |
| BBB | Daily | Indefinite |
| Yellow Pages | Continuous | Indefinite |
| Crunchbase | Daily | Indefinite |

## Compliance Notes

### GDPR Considerations
- Personal data (names, emails, phones) requires consent
- Right to erasure applies to personal data
- Data retention: 2 years default, 7 years for financial

### CCPA Considerations
- California residents have opt-out rights
- Disclosure requirements for data sale

### Terms of Service
- Check each source's ToS before scraping
- Respect robots.txt directives
- Implement rate limiting

## Error Handling

### Common Errors

| Error Type | Cause | Resolution |
|------------|-------|------------|
| 429 Too Many Requests | Rate limiting | Implement backoff |
| 403 Forbidden | Access denied | Add headers, use API |
| 404 Not Found | Resource removed | Remove from pipeline |
| 503 Unavailable | Service down | Retry with delay |

### Retry Strategy
- Max retries: 3
- Backoff: exponential (2^n seconds)
- Timeout: 30 seconds per request
