"""
Free Data Sources Integration
TensorMarketData - Company Data API
"""

import os
from typing import Optional, List, Dict, Any
import httpx

# Yahoo Finance - Free stock data
async def get_company_info(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Get company info from Yahoo Finance (free, no API key needed)
    """
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            data = resp.json()
            
            results = data.get("quoteResponse", {}).get("result", [])
            if results:
                q = results[0]
                return {
                    "ticker": q.get("symbol"),
                    "name": q.get("shortName") or q.get("longName"),
                    "sector": q.get("sector"),
                    "industry": q.get("industry"),
                    "market_cap": q.get("marketCap"),
                    "employees": q.get("fullTimeEmployees"),
                    "description": q.get("description"),
                    "website": q.get("website"),
                    "phone": q.get("phone"),
                    "address": q.get("address1"),
                    "city": q.get("city"),
                    "state": q.get("state"),
                    "country": q.get("country"),
                    "source": "yahoo_finance"
                }
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
    
    return None


async def search_companies(query: str) -> List[Dict[str, Any]]:
    """
    Search for companies - using Yahoo Finance tickers
    """
    # Common tickers for demo
    tickers = [
        "GOOGL", "AAPL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "JPM", 
        "V", "UNH", "HD", "MA", "PG", "JNJ", "BAC", "ADBE", "CRM",
        "NFLX", "DIS", "PYPL", "INTC", "AMD", "ORCL", "IBM", "QCOM"
    ]
    
    results = []
    for ticker in tickers:
        info = await get_company_info(ticker)
        if info and query.lower() in (info.get("name", "") + info.get("sector", "")).lower():
            results.append(info)
    
    return results[:10]


# OpenCorporates - Free company registry
async def get_company_opencorporates(company_number: str, jurisdiction: str = "us") -> Optional[Dict]:
    """
    Get company data from OpenCorporates (free)
    """
    url = f"https://api.opencorporates.com/v0.4/companies/{jurisdiction}/{company_number}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            data = resp.json()
            
            if data.get("results", {}).get("company"):
                c = data["results"]["company"]
                return {
                    "name": c.get("name"),
                    "company_number": c.get("company_number"),
                    "jurisdiction": c.get("jurisdiction_code"),
                    "incorporation_date": c.get("incorporation_date"),
                    "source": "opencorporates"
                }
    except Exception as e:
        print(f"Error fetching OpenCorporates: {e}")
    
    return None


# Sample data for demo
SAMPLE_COMPANIES = [
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc",
        "sector": "Technology",
        "industry": "Internet Services",
        "description": "Technology company specializing in internet services",
        "verified": True
    },
    {
        "ticker": "AAPL", 
        "name": "Apple Inc",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "description": "Designer and marketer of consumer electronics",
        "verified": True
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corporation",
        "sector": "Technology",
        "industry": "Software",
        "description": "Software corporation developing operating systems",
        "verified": True
    },
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc",
        "sector": "Consumer Cyclical",
        "industry": "E-Commerce",
        "description": "E-commerce and cloud computing company",
        "verified": True
    },
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corporation",
        "sector": "Technology",
        "industry": "Semiconductors",
        "description": "GPU and AI chip manufacturer",
        "verified": True
    }
]
