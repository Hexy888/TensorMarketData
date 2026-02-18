# TensorMarketData API Guide

This guide covers the TensorMarketData API for developers building AI agents and data-intensive applications.

## Base URL

```
https://tensormarketdata.com/v1
```

## Authentication

All API requests require an API key. Include it in the `Authorization` header:

```bash
curl -H "Authorization: Bearer $TENSOR_API_KEY" \
  https://tensormarketdata.com/v1/datasets
```

**Security note**: Never expose API keys in client-side code or version control. Use environment variables.

## Rate Limits

| Plan | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 60 | 1,000 |
| Pro | 300 | 50,000 |
| Enterprise | Custom | Custom |

Rate limit status is returned in response headers:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1640995200
```

## Endpoints

### List Available Datasets

```http
GET /datasets
```

Query parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category (ecommerce, finance, social, etc.) |
| `freshness` | string | Filter by update frequency (realtime, hourly, daily) |
| `limit` | integer | Number of results (default: 20, max: 100) |
| `offset` | integer | Pagination offset |

**Response**:

```json
{
  "datasets": [
    {
      "id": "ds_ecommerce_products_001",
      "name": "E-commerce Product Catalog",
      "category": "ecommerce",
      "description": "Structured product data from major retailers",
      "fields": ["product_id", "name", "price", "in_stock", "category", "brand"],
      "record_count": 15000000,
      "freshness": "realtime",
      "update_frequency": "continuous",
      "last_updated": "2024-12-15T10:30:00Z",
      "license": "commercial",
      "pricing_model": "per-query"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Query a Dataset

```http
POST /datasets/{dataset_id}/query
```

**Request body**:

```json
{
  "filters": {
    "field": "category",
    "operator": "eq",
    "value": "electronics"
  },
  "fields": ["product_id", "name", "price", "in_stock"],
  "limit": 100,
  "offset": 0,
  "sort": {
    "field": "price",
    "order": "asc"
  }
}
```

**Filter operators**: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `contains`, `regex`

**Response**:

```json
{
  "data": [
    {
      "product_id": "PROD-001",
      "name": "Wireless Headphones",
      "price": 149.99,
      "in_stock": true
    }
  ],
  "meta": {
    "result_count": 1,
    "total_available": 15234,
    "query_time_ms": 45
  }
}
```

### Get Dataset Schema

```http
GET /datasets/{dataset_id}/schema
```

Returns field definitions, types, and constraints for a dataset.

### Stream Real-Time Data

```http
GET /datasets/{dataset_id}/stream
```

Opens a server-sent events (SSE) stream for real-time data:

```bash
curl -N -H "Authorization: Bearer $TENSOR_API_KEY" \
  https://tensormarketdata.com/v1/datasets/ds_ecommerce_products_001/stream
```

**Stream format**:

```
data: {"product_id":"PROD-002","name":"Bluetooth Speaker","price":79.99,"in_stock":true,"_timestamp":"2024-12-15T10:30:05Z"}

data: {"product_id":"PROD-003","name":"USB-C Hub","price":45.00,"in_stock":false,"_timestamp":"2024-12-15T10:30:06Z"}
```

### Subscribe to Changes

```http
POST /datasets/{dataset_id}/subscribe
```

Subscribe to specific field changes for real-time notification:

```json
{
  "fields": ["price", "in_stock"],
  "filter": {
    "field": "category",
    "operator": "eq",
    "value": "electronics"
  },
  "webhook_url": "https://your-server.com/webhook"
}
```

## Data Types

| Type | Description |
|------|-------------|
| `string` | UTF-8 text |
| `integer` | 64-bit signed integer |
| `float` | IEEE 754 double precision |
| `boolean` | true or false |
| `timestamp` | ISO 8601 datetime |
| `array` | JSON array |
| `object` | Nested JSON object |

## Error Handling

Error responses include `error` object with `code`, `message`, and `details`:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. 300 requests/minute allowed.",
    "details": {
      "retry_after": 30
    }
  }
}
```

**Common error codes**:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | Check your Authorization header |
| `DATASET_NOT_FOUND` | 404 | Dataset ID doesn't exist |
| `INVALID_QUERY` | 400 | Query syntax error |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `QUOTA_EXCEEDED` | 402 | Usage quota reached |
| `SERVER_ERROR` | 500 | Internal error |

## Code Examples

### Python

```python
import requests

TENSOR_API_KEY = os.environ["TENSOR_API_KEY"]
BASE_URL = "https://tensormarketdata.com/v1"

headers = {"Authorization": f"Bearer {TENSOR_API_KEY}"}

# List datasets
response = requests.get(f"{BASE_URL}/datasets", headers=headers)
datasets = response.json()["datasets"]

# Query dataset
query = {
    "filters": {"field": "category", "operator": "eq", "value": "electronics"},
    "fields": ["product_id", "name", "price"],
    "limit": 100
}

response = requests.post(
    f"{BASE_URL}/datasets/ds_ecommerce_products_001/query",
    json=query,
    headers=headers
)
data = response.json()["data"]
```

### JavaScript/Node.js

```javascript
const fetch = require('node-fetch');

const TENSOR_API_KEY = process.env.TENSOR_API_KEY;
const BASE_URL = 'https://tensormarketdata.com/v1';

const headers = { 'Authorization': `Bearer ${TENSOR_API_KEY}` };

// List datasets
const listRes = await fetch(`${BASE_URL}/datasets`, { headers });
const { datasets } = await listRes.json();

// Query dataset
const queryRes = await fetch(
  `${BASE_URL}/datasets/ds_ecommerce_products_001/query`,
  {
    method: 'POST',
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filters: { field: 'category', operator: 'eq', value: 'electronics' },
      fields: ['product_id', 'name', 'price'],
      limit: 100
    })
  }
);
const { data } = await queryRes.json();
```

## Best Practices

1. **Use filtering**: Always filter results server-side rather than fetching all data and filtering client-side.

2. **Specify required fields**: The `fields` parameter reduces response size and improves performance.

3. **Handle pagination**: Use `offset` and `limit` to iterate through large result sets.

4. **Respect rate limits**: Implement exponential backoff when receiving 429 responses.

5. **Cache appropriately**: Dataset metadata changes infrequently. Cache `/datasets` and `/schema` responses.

6. **Monitor usage**: Track `X-RateLimit-*` headers to avoid quota surprises.

## Support

- Documentation: https://docs.tensormarketdata.com
- API Status: https://status.tensormarketdata.com
- Email: support@tensormarketdata.com
