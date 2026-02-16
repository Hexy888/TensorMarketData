# TensorMarketData Python SDK

Official Python client for the TensorMarketData API.

<p align="center">
  <a href="https://pypi.org/project/tensormarket/">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/tensormarket">
  </a>
  <a href="https://pypi.org/project/tensormarket/">
    <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dd/tensormarket">
  </a>
  <a href="https://github.com/TensorMarketData/python-sdk/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/TensorMarketData/python-sdk">
  </a>
</p>

<p align="center">
  <strong>The data layer for AI agents 🚀</strong>
</p>

---

## Features

- 🔍 **Natural Language Search** - Find suppliers with queries like "manufacturers in Ohio"
- 📊 **Inventory Queries** - Check real-time stock and pricing
- 🤖 **AI-Native** - Built for agents, copilots, and autonomous systems
- 💳 **Pay-Per-Use** - No subscriptions, pay only for what you query
- 🔗 **Webhook Integration** - Subscribe to real-time updates

---

## Installation

```bash
pip install tensormarket
```

---

## Quick Start

```python
from tensormarket import TensorMarket

# Initialize with your API key
client = TensorMarket(api_key="tmd_your_key_here")

# Natural language search
results = client.search("software companies in california with 100+ employees")
print(results)

# Get supplier details
supplier = client.get_supplier(supplier_id="uuid-here")
print(supplier)

# Check inventory
inventory = client.get_inventory(supplier_id="uuid-here")
print(inventory)
```

---

## Environment Variables

```bash
export TENSORMARKET_API_KEY="tmd_your_key_here"
```

---

## API Reference

### Search

```python
# Basic search
results = client.search("manufacturers in ohio")

# With filters
results = client.search(
    query="tech companies",
    industry="technology",
    min_employees=100,
    limit=10,
)
```

### Suppliers

```python
# Get supplier by ID
supplier = client.get_supplier(supplier_id="uuid")

# List suppliers
suppliers = client.list_suppliers(limit=50)
```

### Inventory

```python
# Get inventory for supplier
inventory = client.get_inventory(
    supplier_id="uuid",
    category="electronics",
    in_stock=True,
)
```

### Credits

```python
# Check your credit balance
balance = client.get_credit_balance()
print(f"Remaining credits: {balance}")
```

---

## Examples

### AI Agent Integration

```python
from tensormarket import TensorMarket
from langchain.tools import Tool

# Create TensorMarket client
tm = TensorMarket(api_key="your-key")

# Search tool for AI agent
def search_suppliers(query: str) -> str:
    results = tm.search(query)
    return str(results[:5])  # Top 5 results

# Add to your agent
tools = [
    Tool(
        name="supplier_search",
        description="Find B2B suppliers and manufacturers",
        func=search_suppliers,
    ),
]
```

### Webhook Subscription

```python
# Subscribe to updates
subscription = client.webhooks.subscribe(
    url="https://your-agent.com/webhook",
    events=["supplier.updated", "product.new"],
)
print(f"Subscribed! ID: {subscription.id}")
```

---

## Documentation

- [Full Documentation](https://tensormarketdata.com/docs)
- [API Reference](https://tensormarketdata.com/docs/api)
- [Examples](https://github.com/TensorMarketData/python-sdk/tree/main/examples)

---

## Contributing

We welcome contributions!

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Support

- 📧 Email: support@tensormarketdata.com
- 💬 Discord: [Join our community](https://discord.gg/tensormarket)
- 🐛 Issues: [GitHub Issues](https://github.com/TensorMarketData/python-sdk/issues)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## About TensorMarketData

TensorMarketData is a headless B2B data marketplace for AI agents. We provide structured, verified supplier data via API, enabling autonomous agents to find and work with businesses.

**Our Mission:** Give every AI agent access to reliable business data.

**Learn more:** [https://tensormarketdata.com](https://tensormarketdata.com)
