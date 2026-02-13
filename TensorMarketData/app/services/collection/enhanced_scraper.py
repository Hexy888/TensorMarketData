"""
Enhanced Data Collection Service
Improved scrapers for business directories, regulatory filings, and industry databases.
"""

import asyncio
import hashlib
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx


class EnhancedBaseScraper(ABC):
    """Enhanced base class for data scrapers with better error handling."""

    def __init__(self, rate_limit: float = 1.0):
        self.client = httpx.AsyncClient(timeout=30.0, headers=self._get_default_headers())
        self.rate_limit = rate_limit
        self.last_request_time = datetime.utcnow()
        self.stats = {"requests": 0, "success": 0, "errors": 0}

    def _get_default_headers(self) -> Dict:
        """Get default headers to avoid being blocked."""
        return {
            "User-Agent": "TensorMarketData-Collector/1.0 (research purposes)",
            "Accept": "application/json, text/html, */*",
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def _rate_limited_request(self, url: str, **kwargs) -> httpx.Response:
        """Make a rate-limited request."""
        elapsed = (datetime.utcnow() - self.last_request_time).total_seconds()
        if elapsed < self.rate_limit:
            await asyncio.sleep(self.rate_limit - elapsed)

        self.last_request_time = datetime.utcnow()
        self.stats["requests"] += 1

        response = await self.client.get(url, **kwargs)
        self.stats["success"] += 1
        return response

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
                "email": self._validate_email(data.get("email")),
                "phone": self._validate_phone(data.get("phone")),
                "website": self._validate_url(data.get("website")),
                "linkedin": self._validate_url(data.get("linkedin")),
                "address": data.get("address"),
            },
            "company_info": {
                "industry": data.get("industry"),
                "size_estimate": data.get("size_estimate"),
                "founded": data.get("founded"),
                "description": data.get("description"),
            },
            "verification_score": data.get("verification_score", 0.5),
            "source": getattr(self, "source_name", "unknown"),
            "source_url": getattr(self, "source_url", None),
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def _validate_email(self, email: Optional[str]) -> Optional[str]:
        if not email:
            return None
        email = str(email).strip().lower()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return email if re.match(pattern, email) else None

    def _validate_phone(self, phone: Optional[str]) -> Optional[str]:
        if not phone:
            return None
        cleaned = re.sub(r"[^\d\+]", "", str(phone).strip())
        return cleaned if 7 <= len(cleaned) <= 15 else None

    def _validate_url(self, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        url = str(url).strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            parsed = urlparse(url)
            return url if parsed.netloc else None
        except Exception:
            return None


class BetterBusinessBureauScraper(EnhancedBaseScraper):
    """Scrape Better Business Bureau directory."""

    source_name = "bbb"
    source_url = "https://www.bbb.org"

    async def search_companies(self, query: str, location: str = "", limit: int = 50) -> List[Dict]:
        """Search BBB for companies."""
        results = []
        url = f"{self.source_url}/search?find_text={query}&find_loc={location}"

        try:
            response = await self._rate_limited_request(url)
            # Would parse HTML with BeautifulSoup here
            # Placeholder return
            return []
        except Exception as e:
            self.stats["errors"] += 1
            return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape BBB directory."""
        return []


class CrunchbaseScraper(EnhancedBaseScraper):
    """Scrape Crunchbase company data (requires API)."""

    source_name = "crunchbase"
    source_url = "https://www.crunchbase.com"

    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key
        if api_key:
            self.client.headers["Authorization"] = f"Bearer {api_key}"

    async def search_organizations(self, query: str, limit: int = 100) -> List[Dict]:
        """Search Crunchbase for organizations."""
        if not self.api_key:
            return []

        url = f"https://api.crunchbase.com/v3.1/organizations"
        params = {"name": query, "limit": limit}

        try:
            response = await self.client.get(url, params=params)
            if response.status_code == 200:
                return response.json().get("items", [])
        except Exception:
            pass

        return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Crunchbase data."""
        return []


class OpenCorporatesScraper(EnhancedBaseScraper):
    """Scrape OpenCorporates company database."""

    source_name = "opencorporates"
    source_url = "https://opencorporates.com"

    async def search_companies(self, query: str, jurisdiction: str = None, limit: int = 50) -> List[Dict]:
        """Search OpenCorporates for companies."""
        params = {"q": query, "per_page": limit}
        if jurisdiction:
            params["jurisdiction_codes"] = jurisdiction

        url = f"{self.source_url}/companies"
        try:
            response = await self._rate_limited_request(url, params=params)
            # Would parse HTML and extract company data
            return []
        except Exception as e:
            self.stats["errors"] += 1
            return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape OpenCorporates data."""
        return []


class LinkedInSalesNavigatorScraper(EnhancedBaseScraper):
    """LinkedIn data enrichment (uses official API)."""

    source_name = "linkedin_sales"
    source_url = "https://www.linkedin.com"

    def __init__(self, access_token: str = None):
        super().__init__(rate_limit=2.0)
        self.access_token = access_token
        if access_token:
            self.client.headers["Authorization"] = f"Bearer {access_token}"

    async def get_company_details(self, company_id: str) -> Dict:
        """Get company details via LinkedIn API."""
        if not self.access_token:
            return {}

        url = f"{self.source_url}/v2/organizations/{company_id}"
        try:
            response = await self._rate_limited_request(url)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass

        return {}

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape LinkedIn data."""
        return []


class YellowPagesScraper(EnhancedBaseScraper):
    """Scrape Yellow Pages business directory."""

    source_name = "yellowpages"
    source_url = "https://www.yellowpages.com"

    async def search_businesses(self, category: str, location: str, limit: int = 50) -> List[Dict]:
        """Search Yellow Pages for businesses."""
        url = f"{self.source_url}/search?search_terms={category}&geo_location_terms={location}"

        try:
            response = await self._rate_limited_request(url)
            # Would parse HTML results
            return []
        except Exception as e:
            self.stats["errors"] += 1
            return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Yellow Pages data."""
        return []


class MantaScraper(EnhancedBaseScraper):
    """Scrape Manta business directory."""

    source_name = "manta"
    source_url = "https://www.manta.com"

    async def search_companies(self, query: str, location: str = "", limit: int = 50) -> List[Dict]:
        """Search Manta for companies."""
        url = f"{self.source_url}/search"
        params = {"q": query, "loc": location}

        try:
            response = await self._rate_limited_request(url, params=params)
            # Would parse HTML results
            return []
        except Exception as e:
            self.stats["errors"] += 1
            return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Manta data."""
        return []


class IndustryAssociationScraper(EnhancedBaseScraper):
    """Scrape industry association directories."""

    source_name = "industry_association"

    # Known association directories
    ASSOCIATIONS = {
        "tech": ["https://www.techamerica.org", "https://www.iti.org"],
        "healthcare": ["https://www.advamed.org", "https://www.phrma.org"],
        "manufacturing": ["https://www.nam.org", "https://www.mapi.com"],
        "finance": ["https://www.sifma.org", "https://www.aba.com"],
    }

    async def scrape_association_directory(self, url: str, category: str) -> List[Dict]:
        """Scrape an industry association directory."""
        try:
            response = await self._rate_limited_request(url)
            # Would parse directory listings
            return []
        except Exception as e:
            self.stats["errors"] += 1
            return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape all association directories."""
        all_results = []
        for category, urls in self.ASSOCIATIONS.items():
            for url in urls:
                results = await self.scrape_association_directory(url, category)
                all_results.extend(results)
        return all_results


class GovernmentContractorScraper(EnhancedBaseScraper):
    """Scrape government contractor databases (SAM.gov, etc.)."""

    source_name = "gov_contracts"
    source_url = "https://sam.gov"

    async def search_sam_registry(self, keyword: str = "", naics_codes: List[str] = None, limit: int = 100) -> List[Dict]:
        """Search SAM.gov contractor registry."""
        # SAM.gov API endpoint
        url = f"{self.source_url}/api/dataset/v2/qualifications"
        params = {
            "q": keyword,
            "limit": limit,
            "status": "active",
        }
        if naics_codes:
            params["naics"] = ",".join(naics_codes)

        try:
            response = await self._rate_limited_request(url, params=params)
            if response.status_code == 200:
                return response.json().get("results", [])
        except Exception as e:
            self.stats["errors"] += 1

        return []

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape government contractor data."""
        return []


class EDGARScraper(EnhancedBaseScraper):
    """Enhanced SEC EDGAR scraper for company filings."""

    source_name = "sec_edgar"
    source_url = "https://www.sec.gov/edgar"

    async def get_company_filings(self, cik: str) -> List[Dict]:
        """Get recent filings for a company."""
        url = f"{self.source_url}/filings"
        params = {"action": "getcompany", "CIK": cik, "type": "10-K"}

        try:
            response = await self._rate_limited_request(url, params=params)
            # Would parse HTML filings page
            return []
        except Exception as e:
            self.stats["errors"] += 1
            return []

    async def get_company_info(self, cik: str) -> Dict:
        """Get company info from SEC."""
        url = f"{self.source_url}/submissions/CIK{cik.zfill(10)}.json"

        try:
            response = await self._rate_limited_request(url)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            self.stats["errors"] += 1

        return {}

    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape SEC EDGAR data."""
        return []


class DataCollector:
    """
    Enhanced collector that orchestrates multiple scrapers with better error handling.
    """

    def __init__(self):
        self.scrapers: List[EnhancedBaseScraper] = []
        self.stats = {"total_collected": 0, "total_errors": 0, "sources_used": []}

    def add_scraper(self, scraper: EnhancedBaseScraper):
        self.scrapers.append(scraper)

    async def collect_all(self) -> List[Dict[str, Any]]:
        """Run all scrapers and aggregate results."""
        all_data = []
        self.stats["sources_used"] = []

        for scraper in self.scrapers:
            try:
                data = await scraper.scrape()
                all_data.extend(data)
                self.stats["total_collected"] += len(data)
                self.stats["sources_used"].append({
                    "source": getattr(scraper, "source_name", "unknown"),
                    "records": len(data),
                    "errors": scraper.stats["errors"],
                })
            except Exception as e:
                self.stats["total_errors"] += 1
                print(f"Scraper {scraper.source_name} failed: {e}")
            finally:
                await scraper.close()

        return all_data

    async def collect_from_source(self, source_name: str) -> List[Dict[str, Any]]:
        """Collect data from a specific source."""
        for scraper in self.scrapers:
            if getattr(scraper, "source_name", "") == source_name:
                try:
                    return await scraper.scrape()
                finally:
                    await scraper.close()
        return []

    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        return {
            "scrapers_registered": len(self.scrapers),
            **self.stats,
        }


# Convenience function to create collector with common scrapers
def create_default_collector(api_keys: Dict[str, str] = None) -> DataCollector:
    """Create collector with default scrapers."""
    collector = DataCollector()

    # Add government API scrapers
    collector.add_scraper(EDGARScraper())
    collector.add_scraper(GovernmentContractorScraper())

    # Add business directory scrapers
    collector.add_scraper(YellowPagesScraper())
    collector.add_scraper(MantaScraper())
    collector.add_scraper(BetterBusinessBureauScraper())

    # Add industry association scrapers
    collector.add_scraper(IndustryAssociationScraper())

    # Add API-based scrapers (if keys provided)
    if api_keys:
        if api_keys.get("crunchbase"):
            collector.add_scraper(CrunchbaseScraper(api_key=api_keys["crunchbase"]))
        if api_keys.get("linkedin"):
            collector.add_scraper(LinkedInSalesNavigatorScraper(access_token=api_keys["linkedin"]))

    return collector
