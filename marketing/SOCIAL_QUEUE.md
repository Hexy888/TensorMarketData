# TensorMarketData Social Queue

## Twitter Posts (@tensormarket)

### Post 1 - Technical Value / Problem-Solution
**Status:** Draft

Most ML teams spend 60-80% of their time on data acquisition and preprocessing instead of modeling. TensorMarketData standardizes market data ingestion with a unified API across 50+ data sources. Less boilerplate, more experimentation.

### Post 2 - Build-in-Public Update
**Status:** Draft

Week 4 update: Just shipped support for Level 2 order book data with real-time delta updates. Had to rearchitect the streaming layer to handle the throughput. Open sourced the websocket client wrapper if anyone wants to audit it.

### Post 3 - Industry Insight
**Status:** Draft

The financial ML space has a fragmentation problem. Every shop builds their own adapters for the same data vendors. We're betting on composable data pipelines as the antidote—not another proprietary platform.

---

## LinkedIn Post

**Status:** Draft

**Title:** Why We Built TensorMarketData

After 3 years building ML systems at a quantitative fund, I noticed a pattern: every team was solving the same data infrastructure problems in isolation.

The market data landscape is fragmented by design—exchanges, vendors, and data providers each speak their own protocol. Teams large and small burn engineering cycles reinventing the same adapters, handling the same edge cases, and maintaining the same broken parsers.

TensorMarketData started as an internal tool to stop this waste. Today it's a composable data pipeline for financial ML—unifying 50+ data sources through a consistent Python API.

We're not selling "data". We're selling engineering time back to ML teams.

Open to feedback from others in the space—what's the most painful part of your data infrastructure today?

#MachineLearning #FinTech #DataEngineering #OpenSource
