# Getting Started with TensorMarketData

This guide will walk you through setting up TensorMarketData and making your first API calls in less than 15 minutes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** or **Node.js 18+**
- A **TensorMarketData account** (free tier available)
- An **API key** from the console

---

## Step 1: Sign Up and Get API Key

1. Go to [tensormarketdata.com/signup](https://tensormarketdata.com/signup)
2. Create your account
3. Navigate to **Settings → API Keys**
4. Click **Create New API Key**
5. Copy and save your API key securely

---

## Step 2: Install the SDK

### Python

```bash
pip install tensormarketdata
```

### Node.js

```bash
npm install @tensormarketdata/sdk
```

---

## Step 3: Configure Your Environment

### Option A: Environment Variable (Recommended)

```bash
export TENSORMARKETDATA_API_KEY="your_api_key_here"
```

### Option B: Code Configuration

```python
from tensormarketdata import Client

client = Client(api_key="your_api_key_here")
```

---

## Step 4: Your First API Call

Create a file called `quickstart.py`:

```python
from tensormarketdata import Client

# Initialize the client
client = Client()

# Check your account status
status = client.get_status()
print(f"Account: {status['email']}")
print(f"Plan: {status['plan']}")
print(f"API Calls Used: {status['usage']['monthly_calls']}")
```

Run it:

```bash
python quickstart.py
```

---

## Step 5: Search Your First Dataset

Let's search the Wikipedia dataset to find articles about machine learning:

```python
from tensormarketdata import Client

client = Client()

# Search for articles related to "machine learning"
results = client.search(
    query="machine learning applications in healthcare",
    dataset_id="ds_wikipedia_2023",
    top_k=5
)

print("\nSearch Results:")
print("=" * 50)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result.metadata['title']}")
    print(f"   Score: {result.score:.4f}")
    print(f"   URL: {result.metadata.get('url', 'N/A')}")
```

Output:

```
Search Results:
==================================================

1. Machine Learning
   Score: 0.9234
   URL: https://en.wikipedia.org/wiki/Machine_learning

2. Artificial Intelligence in Healthcare
   Score: 0.8912
   URL: https://en.wikipedia.org/wiki/Artificial_intelligence_in_healthcare

3. Deep Learning
   Score: 0.8756
   URL: https://en.wikipedia.org/wiki/Deep_learning
```

---

## Step 6: Generate Your Own Embeddings

Create embeddings for custom text:

```python
from tensormarketdata import Client

client = Client()

# Generate embeddings
texts = [
    "TensorMarketData provides vector search",
    "Embeddings capture semantic meaning",
    "Vector databases power AI applications"
]

result = client.embed(
    texts=texts,
    model="text-embedding-3-small",
    normalize=True
)

print(f"Generated {len(result.embeddings)} embeddings")
print(f"Each embedding has {len(result.embeddings[0])} dimensions")

# Show first 10 dimensions of first embedding
print(f"\nFirst 10 values: {result.embeddings[0][:10]}")
```

---

## Step 7: Build a Simple RAG Application

Combine search and embeddings for Retrieval-Augmented Generation:

```python
from tensormarketdata import Client

client = Client()

class SimpleRAG:
    def __init__(self, dataset_id):
        self.dataset_id = dataset_id
    
    def query(self, question, top_k=3):
        # 1. Convert question to embedding
        embedding = client.embed([question], model="text-embedding-3-small")
        
        # 2. Search for relevant documents
        results = client.search_vectors(
            vector=embedding[0],
            dataset_id=self.dataset_id,
            top_k=top_k
        )
        
        # 3. Return context
        context = "\n\n".join([
            r.metadata.get('text', r.metadata.get('title', ''))
            for r in results
        ])
        
        return {
            "question": question,
            "context": context,
            "sources": [
                {"id": r.id, "score": r.score}
                for r in results
            ]
        }

# Use the RAG system
rag = SimpleRAG("ds_wikipedia_2023")

response = rag.query("What is TensorFlow used for?")

print("Question:", response['question'])
print("\nRetrieved Context:", response['context'][:500])
print("\nSources:", response['sources'])
```

---

## Step 8: Explore Available Datasets

```python
from tensormarketdata import Client

client = Client()

# List available datasets
datasets = client.datasets.list(
    category="text",
    min_quality=4.5,
    limit=10,
    sort_by="quality",
    sort_order="desc"
)

print("Top-Rated Text Datasets:")
print("=" * 60)

for ds in datasets:
    print(f"\n{ds.name}")
    print(f"  Size: {ds.size_gb} GB")
    print(f"  Vectors: {ds.vector_count:,}")
    print(f"  Quality: {ds.quality_score}/5")
    print(f"  Price: ${ds.price['amount']}")
```

---

## Common Patterns

### Pattern 1: Batch Search

```python
from tensormarketdata import Client

client = Client()

# Search multiple queries
queries = [
    "neural network architectures",
    "transformer models explained",
    "reinforcement learning basics"
]

all_results = client.search_batch(
    queries=queries,
    dataset_id="ds_wikipedia_2023",
    top_k=5
)

for query, results in zip(queries, all_results):
    print(f"\nQuery: {query}")
    for r in results:
        print(f"  - {r.metadata['title']} ({r.score:.3f})")
```

### Pattern 2: Async Search

```python
import asyncio
from tensormarketdata import AsyncClient

async def search_all(queries, dataset_id):
    client = AsyncClient()
    tasks = [
        client.search(q, dataset_id=dataset_id)
        for q in queries
    ]
    return await asyncio.gather(*tasks)

# Run concurrent searches
results = asyncio.run(search_all(
    ["AI", "ML", "DL"],
    "ds_wikipedia_2023"
))
```

### Pattern 3: Search with Filters

```python
from tensormarketdata import Client

client = Client()

# Filter by year and category
results = client.search(
    query="climate change",
    dataset_id="ds_wikipedia_2023",
    top_k=10,
    filters={
        "year": {"$gte": 2020},
        "category": "science"
    }
)
```

---

## Next Steps

Now that you've completed the basics, explore:

1. **[Advanced Search Techniques](./advanced-search.md)** - Filters, hybrid search, reranking
2. **[Building RAG Applications](./rag-tutorial.md)** - Full implementation guide
3. **[Dataset Catalog](../api/datasets.md)** - Browse available datasets
4. **[API Reference](../api/overview.md)** - Complete API documentation

---

## Troubleshooting

### "API key not found"

Make sure your API key is set:
```bash
echo $TENSORMARKETDATA_API_KEY
```

### "Dataset not found"

Verify the dataset ID exists:
```python
datasets = client.datasets.list(limit=10)
for ds in datasets:
    print(ds.id, ds.name)
```

### Rate limit errors

Implement exponential backoff:
```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "rate" in str(e).lower():
                wait = (2 ** attempt) * 10
                time.sleep(wait)
            else:
                raise
```

---

## Get Help

- **Documentation**: https://docs.tensormarketdata.com
- **API Reference**: https://api.tensormarketdata.com/docs
- **Discord**: https://discord.gg/tensormarketdata
- **Email**: support@tensormarketdata.com
