# Frequently Asked Questions

## General Questions

### What is TensorMarketData?

TensorMarketData is a B2B data marketplace and vector search platform designed for AI agents and applications. We provide:

- **High-quality datasets** pre-computed with state-of-the-art embeddings
- **Vector search API** for semantic similarity searches
- **Embedding generation** for your own text, images, and data
- **Managed infrastructure** so you can focus on your application

### Who should use TensorMarketData?

TensorMarketData is ideal for:

- **AI/ML Engineers** building semantic search or RAG applications
- **Product Teams** adding intelligent search to their products
- **Data Scientists** needing high-quality training and reference data
- **Startups** building AI agents that need knowledge access
- **Enterprises** modernizing search infrastructure

### How does the pricing work?

We offer usage-based pricing:

| Component | Price |
|-----------|-------|
| Dataset purchases | One-time or subscription (per dataset) |
| Search queries | $0.001 per 1,000 queries |
| Embedding generation | $0.0001 - $0.0013 per 1K tokens |
| Storage | Included for purchased datasets |

**Free tier**: 1,000 searches/day, 100K embedding tokens/month

### What datasets are available?

We have datasets across multiple categories:

- **Text**: Wikipedia, news, academic papers, legal documents, social media
- **Images**: Product images, medical imaging, stock photos
- **Audio**: Speech, music, environmental sounds
- **Multimodal**: Image-text pairs for CLIP training

Browse the [Dataset Catalog](../api/datasets.md) for complete listings.

---

## Technical Questions

### What embedding models do you use?

We offer multiple models:

| Model | Dimension | Best For |
|-------|-----------|----------|
| `text-embedding-3-large` | 1024-3072 | High-quality semantic search |
| `text-embedding-3-small` | 512-1024 | Cost-effective applications |
| `clip-vit-b-32` | 512 | Image-text cross-modal search |
| `e5-large-v2` | 1024 | Multilingual search |

All models are continuously updated with improvements.

### What's the difference between semantic and hybrid search?

| Search Type | Description | Best For |
|-------------|-------------|----------|
| **Semantic** | Uses embeddings to find conceptually similar results | Natural language queries |
| **Keyword** | Traditional BM25 text matching | Exact phrases, proper nouns |
| **Hybrid** | Combines semantic + keyword with weighted scoring | Production systems |

```python
# Semantic search
results = client.search(query="how to bake bread", search_type="semantic")

# Hybrid search
results = client.search(
    query="how to bake bread",
    search_type="hybrid",
    weights={"semantic": 0.7, "keyword": 0.3}
)
```

### What vector dimensions do you support?

| Dataset | Dimensions | Notes |
|---------|------------|-------|
| Text datasets | 1024, 1536, 3072 | Configurable on query |
| Image datasets | 512, 768, 2048 | Model-dependent |
| Custom embeddings | Any | Up to 4096 dimensions |

### How do filters work?

Filters apply metadata constraints to search results:

```python
# Filter by year
results = client.search(
    query="machine learning",
    dataset_id="ds_papers",
    filters={"year": {"$gte": 2020}}
)

# Complex filters
results = client.search(
    query="AI ethics",
    filters={
        "$and": [
            {"year": {"$gte": 2020}},
            {"citations": {"$gte": 100}},
            {"venue": {"$in": ["NeurIPS", "ICML"]}}
        ]
    }
)
```

### What are the rate limits?

| Plan | Searches/min | Embeddings/min |
|------|-------------|----------------|
| Free | 60 | 100 |
| Starter | 300 | 1,000 |
| Professional | 1,000 | 10,000 |
| Enterprise | Custom | Custom |

---

## Integration Questions

### Which SDKs do you support?

- **Python**: `pip install tensormarketdata`
- **Node.js**: `npm install @tensormarketdata/sdk`
- **Go**: `go get github.com/tensormarketdata/sdk-go`
- **Ruby**: `gem install tensormarketdata`
- **REST API**: Full REST endpoints for any language

### How do I get started?

1. [Sign up](https://tensormarketdata.com/signup) for an account
2. Get your API key from the console
3. Install the SDK: `pip install tensormarketdata`
4. Make your first API call!

```python
from tensormarketdata import Client

client = Client()
results = client.search("artificial intelligence", dataset_id="ds_wikipedia_2023")
```

### Can I use my own embedding model?

Yes! You can:

1. **Upload your own embeddings** with your data
2. **Use our API** with external embeddings
3. **Fine-tune models** on your datasets (Enterprise plan)

```python
# Search with your own vectors
results = client.search_vectors(
    vector=your_embedding,
    dataset_id="ds_my_dataset"
)
```

### How do I integrate with LangChain?

```python
from langchain.retrievers import TensorMarketDataRetriever
from langchain_openai import OpenAI
from langchain.chains import RetrievalQA

# Create retriever
retriever = TensorMarketDataRetriever(
    dataset_id="ds_wikipedia_2023",
    api_key="YOUR_API_KEY"
)

# Create QA chain
llm = OpenAI(api_key="OPENAI_API_KEY")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff"
)

# Query
result = qa_chain.invoke({"query": "What is machine learning?"})
```

### How do I integrate with LlamaIndex?

```python
from llama_index import VectorStoreIndex
from llama_index.vector_stores import TensorMarketDataVectorStore

# Create vector store
vector_store = TensorMarketDataVectorStore(
    dataset_id="ds_wikipedia_2023",
    api_key="YOUR_API_KEY"
)

# Create index
index = VectorStoreIndex.from_vector_store(vector_store)

# Query
query_engine = index.as_query_engine()
response = query_engine.query("What are neural networks?")
```

---

## Data Questions

### How is data quality ensured?

| Quality Factor | How We Ensure It |
|----------------|------------------|
| **Completeness** | Automated integrity checks |
| **Consistency** | Schema validation |
| **Freshness** | Regular updates from publishers |
| **Accuracy** | Publisher verification |
| **Relevance** | Community ratings + quality scores |

### How often are datasets updated?

| Dataset Type | Update Frequency |
|--------------|------------------|
| News | Daily |
| Social Media | Hourly |
| Academic | Monthly |
| Encyclopedic | Quarterly |
| Product catalogs | Weekly |

### Can I request a new dataset?

Yes! Submit requests through:

1. **Console**: Dataset → Request Dataset
2. **Email**: datasets@tensormarketdata.com
3. **Community**: Discord #dataset-requests

### What formats are available for download?

| Format | Use Case |
|--------|----------|
| `tar.gz` | Bulk downloads |
| `zip` | Windows compatibility |
| `streaming` | Large datasets |
| `jsonl` | Metadata + vectors |

---

## Security & Compliance

### Is my data secure?

Yes. We implement:

- **Encryption at rest**: AES-256
- **Encryption in transit**: TLS 1.3
- **SOC 2 Type II certified**
- **GDPR compliant**
- **No training on your data**

### Can I use TensorMarketData in regulated industries?

Yes. We support:

- **HIPAA** (Healthcare)
- **FINRA** (Financial Services)
- **FedRAMP** (Government)
- **ISO 27001** certified

Contact enterprise@tensormarketdata.com for compliance documentation.

### Do you share my data?

**Never.** We:

- Do not train models on your queries or data
- Do not share usage patterns
- Do not sell personal data
- Do not use your data for any purpose except serving your requests

See our [Privacy Policy](https://tensormarketdata.com/privacy) for details.

---

## Account & Billing

### How do I upgrade my plan?

1. Go to **Console → Settings → Plan**
2. Select your new plan
3. Billing prorates automatically

### How do I cancel?

1. Go to **Console → Settings → Plan**
2. Select "Cancel Plan"
3. Your access continues until the end of the billing period

### Do you offer refunds?

- **Datasets**: 30-day money-back guarantee
- **Subscriptions**: Prorated refund on cancellation
- **Usage charges**: No refunds

### How do I get an invoice?

Invoices are generated automatically:

1. **Console → Billing → Invoices**
2. Download PDF invoices
3. Set up billing emails in settings

---

## Troubleshooting

### "API key not found"

**Cause**: API key not set or incorrect.

**Solution**:
```bash
# Check if key is set
echo $TENSORMARKETDATA_API_KEY

# Set the key
export TENSORMARKETDATA_API_KEY="your_key_here"
```

Or in code:
```python
client = Client(api_key="your_key_here")
```

### "Dataset not found"

**Cause**: Incorrect dataset ID.

**Solution**:
```python
# List available datasets
datasets = client.datasets.list(limit=100)
for ds in datasets:
    print(ds.id, ds.name)
```

### "Rate limit exceeded"

**Cause**: Too many requests.

**Solution**:
```python
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "rate" in str(e).lower():
                wait = (2 ** i) * 10
                print(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
```

### "Invalid vector dimension"

**Cause**: Vector dimension doesn't match dataset.

**Solution**:
```python
# Check dataset embedding dimension
dataset = client.datasets.get(dataset_id)
print(f"Embedding dimension: {dataset['embedding_dimension']}")

# Ensure your vectors match
embedding = client.embed(texts=[text], model=dataset['embedding_model'])
```

### Slow response times

**Cause**: Large queries, network issues, or high load.

**Solutions**:
1. Reduce `top_k` parameter
2. Use async requests for batches
3. Implement caching:
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_search(query: str):
    return client.search(query, dataset_id="ds_1")
```

### Empty search results

**Cause**: Too restrictive filters or low score threshold.

**Solution**:
```python
# Remove filters
results = client.search(query, dataset_id)

# Lower score threshold
results = client.search(query, dataset_id, score_threshold=0.1)

# Try different query phrasing
results = client.search("alternative query terms", dataset_id)
```

---

## Still Have Questions?

- **Documentation**: https://docs.tensormarketdata.com
- **API Reference**: https://tensormarketdata.com/docs
- **Discord**: https://discord.gg/tensormarketdata
- **Email**: support@tensormarketdata.com
- **Sales**: sales@tensormarketdata.com
