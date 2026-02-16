"""
Data Collection Service
Scrapes public directories and government APIs for supplier data.
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from app.core.config import settings


class BaseScraper(ABC):
    """Base class for data scrapers."""

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape and return supplier data."""
        pass

    async def close(self):
        await self.client.aclose()

    def validate_supplier(self, data: Dict) -> Optional[Dict]:
        """Validate and normalize supplier data."""
        required = ["name"]
        for field in required:
            if not data.get(field):
                return None

        return {
            "name": data["name"].strip(),
            "contact_json": {
                "email": data.get("email"),
                "phone": data.get("phone"),
                "linkedin": data.get("linkedin"),
            },
            "verification_score": data.get("verification_score", 0.5),
            "source": getattr(self, "source_name", "unknown"),
            "scraped_at": datetime.utcnow().isoformat(),
        }


class GovernmentAPIScraper(BaseScraper):
    """Base scraper for government data sources."""

    async def fetch_json(self, url: str, params: Dict = None) -> List[Dict]:
        """Fetch JSON from API."""
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()


class SECScraper(GovernmentAPIScraper):
    """Scrape SEC company filings."""

    source_name = "sec"
    BASE_URL = "https://data.sec.gov"

    async def get_company(self, cik: str) -> Dict:
        """Get company info by CIK."""
        url = f"{self.BASE_URL}/submissions/CIK{cik.zfill(10)}.json"
        data = await self.fetch_json(url)
        return data

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape SEC company data."""
        # In production, would iterate through a list of CIKs
        return []


class FDAScraper(GovernmentAPIScraper):
    """Scrape FDA establishment registrations."""

    source_name = "fda"
    BASE_URL = "https://api.fda.gov"

    async def search_companies(self, query: str, limit: int = 100) -> List[Dict]:
        """Search FDA device registrations."""
        url = f"{self.BASE_URL}/device/registrationlisting.json"
        params = {"search": query, "limit": limit}
        return await self.fetch_json(url, params)

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape FDA registered companies."""
        return []


class LinkedInScraper(BaseScraper):
    """LinkedIn company data scraper."""

    source_name = "linkedin"

    async def scrape_company(self, company_url: str) -> Dict:
        """Scrape company info from LinkedIn URL."""
        # Note: LinkedIn has strict anti-scraping
        # In production, would use official API or proxy
        return {}

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape company data."""
        return []


class DirectoryScraper(BaseScraper):
    """Generic business directory scraper."""

    source_name = "directory"

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url

    async def scrape_directory(self, category: str = None) -> List[Dict]:
        """Scrape a business directory."""
        url = self.base_url
        if category:
            url = f"{self.base_url}/{category}"

        response = await self.client.get(url)
        response.raise_for_status()

        # Parse HTML (would use BeautifulSoup in production)
        return self.parse_results(response.text)

    def parse_results(self, html: str) -> List[Dict]:
        """Parse directory listing from HTML."""
        # Placeholder - would use BeautifulSoup
        return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape directory."""
        return []


class DataCollector:
    """
    Main collector that orchestrates multiple scrapers.
    """

    def __init__(self):
        self.scrapers: List[BaseScraper] = []

    def add_scraper(self, scraper: BaseScraper):
        self.scrapers.append(scraper)

    async def collect_all(self) -> List[Dict[str, Any]]:
        """Run all scrapers and aggregate results."""
        all_data = []

        for scraper in self.scrapers:
            try:
                data = await scraper.scrape()
                all_data.extend(data)
            except Exception as e:
                print(f"Scraper {scraper.source_name} failed: {e}")
            finally:
                await scraper.close()

        return all_data

    async def run_single(self, scraper: BaseScraper) -> List[Dict[str, Any]]:
        """Run a single scraper."""
        try:
            return await scraper.scrape()
        finally:
            await scraper.close()


# Convenience functions
async def collect_from_apis() -> List[Dict[str, Any]]:
    """Collect data from government APIs."""
    collector = DataCollector()
    collector.add_scraper(SECScraper())
    collector.add_scraper(FDAScraper())
    return await collector.collect_all()


async def collect_from_directory(base_url: str, category: str = None) -> List[Dict[str, Any]]:
    """Collect data from a business directory."""
    scraper = DirectoryScraper(base_url)
    return await scraper.scrape()
