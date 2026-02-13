"""
Data Enrichment Service
Enriches supplier data with additional information from external sources.
"""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
import re


class CompanyAPIClient:
    """
    Client for company data enrichment APIs.
    Supports multiple providers (Clearbit, FullContact, etc.)
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.providers = {
            "clearbit": self._enrich_clearbit,
            "fullcontact": self._enrich_fullcontact,
            "duckduckgo": self._enrich_duckduckgo,
        }

    async def enrich_company(self, company_data: Dict) -> Dict:
        """Enrich company data using available APIs."""
        enriched = company_data.copy()
        enriched["enrichment"] = {}

        # Try each provider
        for provider, enrich_func in self.providers.items():
            try:
                result = await enrich_func(company_data)
                if result:
                    enriched["enrichment"][provider] = result
            except Exception as e:
                enriched["enrichment"][provider] = {"error": str(e)}

        return enriched

    async def _enrich_clearbit(self, data: Dict) -> Optional[Dict]:
        """Enrich using Clearbit API (placeholder)."""
        # Clearbit API integration would go here
        # API: https://dashboard.clearbit.com/docs/api
        domain = self._extract_domain(data)
        if not domain:
            return None

        # Placeholder - actual API call would be:
        # response = await self.client.get(f"https://company.clearbit.com/v2/companies/find?domain={domain}", headers={"Authorization": f"Bearer {self.api_key}"})
        return {"domain": domain, "status": "api_key_required"}

    async def _enrich_fullcontact(self, data: Dict) -> Optional[Dict]:
        """Enrich using FullContact API (placeholder)."""
        # FullContact API integration would go here
        email = data.get("email") or data.get("contact_json", {}).get("email")
        if not email:
            return None

        return {"email": email, "status": "api_key_required"}

    async def _enrich_duckduckgo(self, data: Dict) -> Optional[Dict]:
        """Enrich using DuckDuckGo instant answer API."""
        domain = self._extract_domain(data)
        if not domain:
            return None

        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.duckduckgo.com/",
                    params={"q": f"{data.get('name', '')} company", "format": "json"},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "abstract": data.get("Abstract"),
                        "categories": data.get("RelatedTopics", [])[:3],
                    }
        except Exception:
            pass

        return None

    def _extract_domain(self, data: Dict) -> Optional[str]:
        """Extract domain from company data."""
        website = data.get("website") or data.get("linkedin", "")
        if website:
            # Extract domain from URL
            match = re.search(r"(?:https?://)?(?:www\.)?([^\s/]+)", website)
            if match:
                domain = match.group(1)
                # Remove www. prefix
                if domain.startswith("www."):
                    domain = domain[4:]
                return domain
        return None


class SocialSignalsEnricher:
    """
    Enriches data with social media signals and web presence.
    """

    def __init__(self):
        self.social_patterns = {
            "linkedin": r"(?:linkedin\.com/|linkedin\.com/company/)([a-zA-Z0-9_-]+)",
            "twitter": r"(?:twitter\.com/|x\.com/)([a-zA-Z0-9_]+)",
            "facebook": r"(?:facebook\.com/|facebook\.com/pages/)([a-zA-Z0-9.-]+)",
            "github": r"github\.com/([a-zA-Z0-9_-]+)",
            "instagram": r"instagram\.com/([a-zA-Z0-9_.]+)",
        }

    def extract_social_handles(self, data: Dict) -> Dict:
        """Extract social media handles from text fields."""
        handles = {}

        text_fields = ["linkedin", "website", "description", "bio"]
        combined_text = " ".join(
            str(data.get(field, "")) for field in text_fields
        )

        for platform, pattern in self.social_patterns.items():
            match = re.search(pattern, combined_text, re.IGNORECASE)
            if match:
                handles[platform] = match.group(1)

        return handles

    def assess_web_presence(self, data: Dict) -> Dict:
        """Assess company's web presence strength."""
        signals = {
            "has_website": bool(data.get("website")),
            "has_linkedin": bool(data.get("linkedin")),
            "has_email": bool(data.get("email") or data.get("contact_json", {}).get("email")),
            "has_phone": bool(data.get("phone") or data.get("contact_json", {}).get("phone")),
        }

        # Calculate presence score
        present_count = sum(1 for v in signals.values() if v)
        presence_score = present_count / len(signals)

        # Determine presence level
        if presence_score >= 0.75:
            level = "strong"
        elif presence_score >= 0.5:
            level = "moderate"
        elif presence_score >= 0.25:
            level = "weak"
        else:
            level = "minimal"

        return {
            "signals": signals,
            "presence_score": round(presence_score, 2),
            "presence_level": level,
        }

    def enrich_social_data(self, data: Dict) -> Dict:
        """Add social enrichment data."""
        handles = self.extract_social_handles(data)
        presence = self.assess_web_presence(data)

        return {
            "social_handles": handles,
            "web_presence": presence,
        }


class NewsFeedEnricher:
    """
    Enriches data with news and recent activity signals.
    """

    def __init__(self):
        self.client = None  # Would initialize news API client

    async def fetch_company_news(self, company_name: str, limit: int = 5) -> List[Dict]:
        """Fetch recent news about a company."""
        # News API integration would go here
        # Providers: NewsAPI, GDELT, Bing News Search
        return []

    def assess_news_sentiment(self, news_items: List[Dict]) -> Dict:
        """Assess sentiment of news coverage."""
        if not news_items:
            return {"sentiment": "unknown", "score": 0.5, "article_count": 0}

        # Placeholder sentiment analysis
        # In production, would use NLP model or sentiment API
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "article_count": len(news_items),
        }

    def calculate_recency_score(self, news_items: List[Dict]) -> float:
        """Calculate how recently company has been in news."""
        if not news_items:
            return 0.0

        from datetime import datetime, timedelta

        # Find most recent article
        most_recent = None
        for item in news_items:
            pub_date = item.get("published_at")
            if pub_date:
                try:
                    if isinstance(pub_date, str):
                        pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    if most_recent is None or pub_date > most_recent:
                        most_recent = pub_date
                except Exception:
                    pass

        if not most_recent:
            return 0.5

        days_ago = (datetime.utcnow() - most_recent).days

        if days_ago <= 7:
            return 1.0
        elif days_ago <= 30:
            return 0.8
        elif days_ago <= 90:
            return 0.6
        elif days_ago <= 180:
            return 0.4
        else:
            return 0.2


class DataEnrichmentPipeline:
    """
    Main enrichment pipeline that orchestrates multiple enrichment sources.
    """

    def __init__(self, api_keys: Dict[str, str] = None):
        self.company_api = CompanyAPIClient(api_key=api_keys.get("clearbit") if api_keys else None)
        self.social_enricher = SocialSignalsEnricher()
        self.news_enricher = NewsFeedEnricher()

    async def enrich_supplier(self, supplier_data: Dict) -> Dict:
        """Run complete enrichment on supplier data."""
        enriched = supplier_data.copy()
        enriched["enrichment_history"] = []

        # Social enrichment (fast, no API needed)
        social_data = self.social_enricher.enrich_social_data(supplier_data)
        enriched.update(social_data)
        enriched["enrichment_history"].append({
            "type": "social",
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
        })

        # Company API enrichment (requires API key)
        if self.company_api.api_key:
            try:
                api_enriched = await self.company_api.enrich_company(supplier_data)
                enriched["api_enrichment"] = api_enriched.get("enrichment", {})
                enriched["enrichment_history"].append({
                    "type": "company_api",
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": True,
                })
            except Exception as e:
                enriched["enrichment_history"].append({
                    "type": "company_api",
                    "timestamp": datetime.utcnow().isoformat(),
                    "success": False,
                    "error": str(e),
                })

        # News enrichment (async)
        news = await self.news_enricher.fetch_company_news(supplier_data.get("name", ""))
        enriched["news"] = news
        enriched["news_sentiment"] = self.news_enricher.assess_news_sentiment(news)
        enriched["news_recency_score"] = self.news_enricher.calculate_recency_score(news)

        return enriched

    async def enrich_batch(self, suppliers: List[Dict], max_concurrent: int = 10) -> List[Dict]:
        """Enrich a batch of suppliers."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_with_limit(supplier):
            async with semaphore:
                return await self.enrich_supplier(supplier)

        results = await asyncio.gather(
            *[enrich_with_limit(s) for s in suppliers],
            return_exceptions=True
        )

        return [r if isinstance(r, Exception) else r for r in results]


# Convenience functions
async def enrich_company_data(company_data: Dict, api_keys: Dict = None) -> Dict:
    """Quick function to enrich a single company."""
    pipeline = DataEnrichmentPipeline(api_keys)
    return await pipeline.enrich_supplier(company_data)


async def enrich_batch_companies(companies: List[Dict], api_keys: Dict = None) -> List[Dict]:
    """Quick function to enrich a batch of companies."""
    pipeline = DataEnrichmentPipeline(api_keys)
    return await pipeline.enrich_batch(companies)
