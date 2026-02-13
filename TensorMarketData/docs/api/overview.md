# TensorMarketData API Documentation

## Overview

Welcome to the TensorMarketData API documentation. Our REST API provides programmatic access to TensorMarketData's vector search and data marketplace capabilities, enabling developers to integrate high-quality vector embeddings and datasets into their AI applications.

### Base URL

```
https://api.tensormarketdata.com/v1
```

### Key Features

- **Vector Search**: Perform semantic similarity searches across millions of vectors
- **Dataset Management**: Browse, purchase, and download datasets
- **Embedding Generation**: Generate embeddings using state-of-the-art models
- **Real-time Updates**: Webhook support for dataset changes and search updates
- **Multi-tenancy**: Organize resources by projects and teams

### Getting Started

1. [Sign up](https://tensormarketdata.com/signup) for a TensorMarketData account
2. [Create an API key](https://console.tensormarketdata.com/settings/api-keys) in the console
3. Install the SDK: `pip install tensormarketdata` or `npm install @tensormarketdata/sdk`
4. Follow our [Getting Started Guide](../tutorials/getting-started.md)

---

## Authentication

All API requests require authentication using an API key. Include your API key in the `Authorization` header of each request.

### Authentication Header

```
Authorization: Bearer YOUR_API_KEY
```

### Example Request

```bash
curl -X GET "https://api.tensormarketdata.com/v1/datasets" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

### API Key Security

- **Never expose your API key** in client-side code or public repositories
- Use environment variables: `TENSORMARKETDATA_API_KEY`
- Rotate keys immediately if compromised
- Create separate keys for development and production

### Rate Limits

| Plan | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Free | 60 | 1,000 |
| Starter | 300 | 50,000 |
| Professional | 1,000 | 1,000,000 |
| Enterprise | Custom | Custom |

---

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "The provided API key is invalid or has been revoked.",
    "status": 401,
    "details": {
      "key_id": "ak_abc123"
    }
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_API_KEY` | 401 | Authentication failed |
| `RATE_LIMITED` | 429 | Too many requests |
| `DATASET_NOT_FOUND` | 404 | Dataset doesn't exist |
| `QUOTA_EXCEEDED` | 403 | Usage limit reached |
| `INVALID_VECTOR` | 400 | Vector dimension mismatch |
| `PAYMENT_REQUIRED` | 402 | Subscription required |

---

## SDK Installation

### Python

```bash
pip install tensormarketdata
```

```python
import tensormarketdata as tmd

client = tmd.Client(api_key="YOUR_API_KEY")
```

### Node.js

```bash
npm install @tensormarketdata/sdk
```

```javascript
const { TensorMarketData } = require('@tensormarketdata/sdk');

const client = new TensorMarketData({ apiKey: 'YOUR_API_KEY' });
```

---

## Quick Start Examples

### Search for Similar Vectors

```python
import tensormarketdata as tmd

client = tmd.Client()

# Search for similar vectors
results = client.search(
    query="machine learning algorithms",
    dataset_id="ds_pubmed_abstracts",
    top_k=10
)

for result in results:
    print(f"Score: {result.score:.4f} | ID: {result.id}")
```

### Download a Dataset

```python
# List available datasets
datasets = client.datasets.list(
    category="text",
    min_size_gb=1
)

# Purchase and download
for ds in datasets:
    if ds.id == "ds_wikipedia_2023":
        client.datasets.download(ds.id, path="./data/")
        break
```

### Generate Embeddings

```python
# Generate embeddings for text
embeddings = client.embed(
    texts=[
        "Deep learning transforms AI applications",
        "Neural networks excel at pattern recognition"
    ],
    model="text-embedding-3-large"
)

print(f"Generated {len(embeddings)} embeddings of dimension {len(embeddings[0])}")
```

---

## Support

- **Documentation**: https://docs.tensormarketdata.com
- **API Reference**: https://api.tensormarketdata.com/docs
- **Support Email**: support@tensormarketdata.com
- **Discord Community**: https://discord.gg/tensormarketdata
