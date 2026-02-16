"""
Data Validation Service
Validates, deduplicates, and enriches supplier data.
"""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.core.config import settings


class DataValidator:
    """
    Validates and cleanses supplier data.
    """

    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")
    URL_PATTERN = re.compile(r"^https?://[\w\-\.]+(\.[\w\-\.]+)+(/[^\s]*)?$")

    def validate_email(self, email: Optional[str]) -> Optional[str]:
        """Validate and normalize email."""
        if not email:
            return None
        email = email.strip().lower()
        if self.EMAIL_PATTERN.match(email):
            return email
        return None

    def validate_phone(self, phone: Optional[str]) -> Optional[str]:
        """Validate and normalize phone number."""
        if not phone:
            return None
        # Remove non-numeric except +
        cleaned = re.sub(r"[^\d\+]", "", phone.strip())
        if 7 <= len(cleaned) <= 15:
            return cleaned
        return None

    def validate_url(self, url: Optional[str]) -> Optional[str]:
        """Validate URL."""
        if not url:
            return None
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        if self.URL_PATTERN.match(url):
            return url
        return None

    def validate_score(self, score: Any) -> float:
        """Validate verification score (0.0 - 1.0)."""
        try:
            s = float(score)
            return max(0.0, min(1.0, s))
        except (TypeError, ValueError):
            return 0.5

    def validate_supplier(self, data: Dict) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a supplier record.
        Returns (is_valid, cleaned_data).
        """
        # Check required fields
        if not data.get("name") or len(data["name"].strip()) < 2:
            return False, None

        cleaned = {
            "name": data["name"].strip(),
            "contact_json": {
                "email": self.validate_email(data.get("email")),
                "phone": self.validate_phone(data.get("phone")),
                "linkedin": self.validate_url(data.get("linkedin")),
            },
            "verification_score": self.validate_score(data.get("verification_score", 0.5)),
            "source": data.get("source", "unknown"),
        }

        # Add metadata
        cleaned["raw_data"] = data.get("raw_data")
        cleaned["scraped_at"] = data.get("scraped_at") or datetime.utcnow().isoformat()

        return True, cleaned


class Deduplicator:
    """
    Detects and removes duplicate supplier records.
    """

    def __init__(self):
        self.validator = DataValidator()

    def generate_fingerprint(self, data: Dict) -> str:
        """Generate a fingerprint for deduplication."""
        name = data.get("name", "").lower().strip()
        email = data.get("contact_json", {}).get("email") or ""

        # Normalize name (remove common suffixes)
        for suffix in ["inc", "llc", "corp", "corporation", "ltd", "co", "company"]:
            name = re.sub(rf"\b{suffix}\b\.?$", "", name)

        # Create fingerprint
        fingerprint = f"{name.strip()}:{email.split('@')[0] if email else ''}"
        return hashlib.md5(fingerprint.encode()).hexdigest()

    def find_duplicates(self, records: List[Dict]) -> List[List[Dict]]:
        """Find groups of duplicate records."""
        fingerprints: Dict[str, List[Dict]] = {}

        for record in records:
            is_valid, cleaned = self.validator.validate_supplier(record)
            if not is_valid:
                continue

            fp = self.generate_fingerprint(cleaned)
            if fp not in fingerprints:
                fingerprints[fp] = []
            fingerprints[fp].append(cleaned)

        # Return only groups with potential duplicates
        return [records for records in fingerprints.values() if len(records) > 1]

    def deduplicate(self, records: List[Dict]) -> List[Dict]:
        """
        Deduplicate records, keeping the best one.
        Returns unique records with merge info.
        """
        fingerprints: Dict[str, Dict] = {}

        for record in records:
            is_valid, cleaned = self.validator.validate_supplier(record)
            if not is_valid:
                continue

            fp = self.generate_fingerprint(cleaned)

            # Keep record with highest verification score
            if fp not in fingerprints:
                fingerprints[fp] = cleaned
            else:
                existing = fingerprints[fp]
                if cleaned.get("verification_score", 0) > existing.get("verification_score", 0):
                    # Merge data, preferring higher-score fields
                    for key in ["contact_json"]:
                        if key in cleaned and cleaned[key]:
                            existing[key] = cleaned[key]
                    existing["verification_score"] = cleaned["verification_score"]
                    existing["source"] = f"{existing.get('source')}+{cleaned.get('source')}"

        return list(fingerprints.values())


class DataEnricher:
    """
    Enriches supplier data with additional fields.
    """

    def enrich(self, data: Dict) -> Dict:
        """Add computed fields to supplier data."""
        # Add industry classification if missing
        if not data.get("industry"):
            data["industry"] = self.classify_industry(data.get("name", ""))

        # Add size estimate based on available data
        if not data.get("size_estimate"):
            data["size_estimate"] = self.estimate_size(data)

        return data

    def classify_industry(self, name: str) -> str:
        """Simple industry classification based on name keywords."""
        name_lower = name.lower()

        keywords = {
            "technology": ["tech", "software", "digital", "computer", "data", "ai", "cloud"],
            "manufacturing": ["mfg", "manufacturing", "factory", "industrial", "parts"],
            "healthcare": ["health", "medical", "pharma", "bio", "hospital", "clinic"],
            "retail": ["retail", "store", "shop", "e-commerce", "marketplace"],
            "finance": ["bank", "finance", "insurance", "capital", "investment"],
            "professional": ["consulting", "services", "agency", "solutions"],
        }

        for industry, words in keywords.items():
            for word in words:
                if word in name_lower:
                    return industry

        return "other"

    def estimate_size(self, data: Dict) -> str:
        """Estimate company size based on available signals."""
        name = data.get("name", "").lower()

        # Check name for size indicators
        if any(x in name for x in ["enterprise", "global", "international"]):
            return "large"
        if any(x in name for x in ["startup", "ventures", "labs"]):
            return "small"
        if any(x in name for x in ["inc", "llc", "corp"]):
            return "medium"

        # Default based on verification
        score = data.get("verification_score", 0.5)
        if score > 0.8:
            return "medium"
        return "unknown"


# Pipeline function
async def process_data(raw_records: List[Dict]) -> List[Dict]:
    """
    Process raw data through validation and deduplication.
    """
    # Validate
    validator = DataValidator()
    valid_records = []
    for record in raw_records:
        is_valid, cleaned = validator.validate_supplier(record)
        if is_valid:
            valid_records.append(cleaned)

    # Deduplicate
    deduplicator = Deduplicator()
    unique_records = deduplicator.deduplicate(valid_records)

    # Enrich
    enricher = DataEnricher()
    enriched_records = [enricher.enrich(r) for r in unique_records]

    return enriched_records
