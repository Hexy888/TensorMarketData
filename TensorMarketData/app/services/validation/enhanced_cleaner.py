"""
Enhanced Data Validation Service
Advanced validation, deduplication, and data cleansing pipeline.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import uuid


@dataclass
class ValidationResult:
    """Result of validation check."""
    is_valid: bool
    cleaned_value: Any
    errors: List[str]
    warnings: List[str]
    score: float  # 0-1 confidence score


class EnhancedEmailValidator:
    """Enhanced email validation with deliverability checks."""

    def __init__(self):
        # RFC 5322 inspired pattern
        self.pattern = re.compile(
            r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
            r"[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
        )
        self.disposable_domains = {
            "mailinator.com", "temp-mail.org", "guerrillamail.com",
            "10minutemail.com", "sharklasers.com", "throwawaymail.com",
        }

    def validate(self, email: Optional[str]) -> ValidationResult:
        """Validate email address."""
        if not email:
            return ValidationResult(False, None, ["Email is required"], [], 0.0)

        email = str(email).strip().lower()

        if len(email) > 254:
            return ValidationResult(False, None, ["Email too long"], [], 0.1)

        if "@" not in email:
            return ValidationResult(False, None, ["Invalid email format"], [], 0.0)

        parts = email.split("@")
        if len(parts) != 2:
            return ValidationResult(False, None, ["Invalid email format"], [], 0.0)

        domain = parts[1]

        if domain in self.disposable_domains:
            return ValidationResult(
                False, email, ["Disposable email detected"], [], 0.1
            )

        if not self.pattern.match(email):
            return ValidationResult(
                False, email, ["Email format invalid"], [], 0.2
            )

        # Basic validation passed
        return ValidationResult(True, email, [], ["Consider verification"], 0.85)


class EnhancedPhoneValidator:
    """Enhanced phone number validation with format detection."""

    # Country code patterns
    COUNTRY_PATTERNS = {
        "US": r"^\+?1?\d{10,14}$",
        "UK": r"^\+?44\d{10,13}$",
        "EU": r"^\+?\d{10,15}$",
    }

    def validate(self, phone: Optional[str], country: str = "US") -> ValidationResult:
        """Validate phone number."""
        if not phone:
            return ValidationResult(False, None, ["Phone is required"], [], 0.0)

        phone = str(phone).strip()

        # Remove all non-numeric except +
        cleaned = re.sub(r"[^\d\+]", "", phone)

        # Check length
        if len(cleaned) < 7:
            return ValidationResult(False, None, ["Phone too short"], [], 0.1)

        if len(cleaned) > 15:
            return ValidationResult(False, None, ["Phone too long"], [], 0.1)

        # Add country code if missing
        if not cleaned.startswith("+"):
            if country == "US" and len(cleaned) == 10:
                cleaned = "+1" + cleaned
            else:
                cleaned = "+" + cleaned

        # Validate format based on country
        pattern = self.COUNTRY_PATTERNS.get(country, self.COUNTRY_PATTERNS["EU"])
        if not re.match(pattern, cleaned):
            return ValidationResult(
                False, cleaned, ["Invalid phone format for region"], [], 0.3
            )

        return ValidationResult(True, cleaned, [], [], 0.9)


class AddressValidator:
    """Address validation and normalization."""

    def validate(self, address: Optional[Dict]) -> ValidationResult:
        """Validate address dictionary."""
        if not address:
            return ValidationResult(True, None, [], [], 0.5)

        required = ["street", "city", "country"]
        warnings = []

        for field in required:
            if not address.get(field):
                return ValidationResult(
                    False, None, [f"Missing required field: {field}"], [], 0.0
                )

        # Normalize
        normalized = {
            "street": address.get("street", "").strip(),
            "city": address.get("city", "").strip(),
            "state": address.get("state", "").strip().upper(),
            "country": address.get("country", "").strip(),
            "postal_code": address.get("postal_code", "").strip(),
        }

        # Check postal code format
        if normalized["country"] == "US":
            if not re.match(r"^\d{5}(-\d{4})?$", normalized["postal_code"]):
                warnings.append("Check US postal code format")

        return ValidationResult(True, normalized, [], warnings, 0.85)


class CompanyNameNormalizer:
    """Normalize and standardize company names."""

    # Common suffixes to remove/standardize
    SUFFIXES = [
        ("inc", "Inc."),
        ("inc.", "Inc."),
        ("llc", "LLC"),
        ("llc.", "LLC"),
        ("corp", "Corp."),
        ("corp.", "Corp."),
        ("corporation", "Corp."),
        ("ltd", "Ltd."),
        ("ltd.", "Ltd."),
        ("co", "Co."),
        ("co.", "Co."),
        ("company", "Co."),
        ("limited", "Ltd."),
    ]

    # Legal entity types
    ENTITY_TYPES = {
        "inc": "corporation",
        "llc": "llc",
        "corp": "corporation",
        "ltd": "limited",
        "lp": "limited_partnership",
        "gp": "general_partnership",
        "sole": "sole_proprietorship",
    }

    def normalize(self, name: str) -> Tuple[str, str, float]:
        """
        Normalize company name.
        Returns (normalized_name, entity_type, confidence).
        """
        if not name:
            return "", "unknown", 0.0

        name = str(name).strip()
        original = name

        # Convert to title case (preserving acronyms)
        words = name.split()
        normalized_words = []

        for word in words:
            if len(word) <= 2 and word.isupper():
                normalized_words.append(word)
            else:
                normalized_words.append(word.capitalize())

        name = " ".join(normalized_words)

        # Replace suffixes
        entity_type = "unknown"
        for old_suffix, new_suffix in self.SUFFIXES:
            pattern = r"\b" + re.escape(old_suffix) + r"\.?$"
            if re.search(pattern, name, re.IGNORECASE):
                name = re.sub(pattern, new_suffix, name, flags=re.IGNORECASE)
                entity_type = self.ENTITY_TYPES.get(old_suffix, "other")
                break

        # Check for parenthetical terms
        paren_match = re.search(r"\((.*?)\)", name)
        if paren_match:
            paren_content = paren_match.group(1)
            if paren_content.lower() in ["formerly", "formerly known as"]:
                name = re.sub(r"\s*\(.*?\)", "", name)

        # Calculate confidence
        confidence = 0.5
        if name != original:
            confidence += 0.2
        if entity_type != "unknown":
            confidence += 0.2
        if len(name) >= 3:
            confidence += 0.1

        return name.strip(), entity_type, min(1.0, confidence)


class EnhancedDeduplicator:
    """Enhanced deduplication with fuzzy matching."""

    def __init__(self):
        self.name_normalizer = CompanyNameNormalizer()

    def generate_fingerprint(self, data: Dict) -> str:
        """Generate fingerprint for deduplication."""
        name = data.get("name", "").lower().strip()
        normalized_name, _, _ = self.name_normalizer.normalize(name)

        # Remove common words
        stop_words = {"the", "a", "an", "of", "for", "and", "group", "holdings"}
        words = normalized_name.lower().split()
        words = [w for w in words if w not in stop_words]

        # Get email domain if available
        email = data.get("email") or data.get("contact_json", {}).get("email", "")
        domain = email.split("@")[-1] if "@" in email else ""

        fingerprint = f"{' '.join(words)}:{domain}"
        return hashlib.md5(fingerprint.encode()).hexdigest()[:16]

    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity using Levenshtein distance."""
        if not name1 or not name2:
            return 0.0

        name1 = name1.lower().strip()
        name2 = name2.lower().strip()

        if name1 == name2:
            return 1.0

        # Simple character-based similarity
        len1, len2 = len(name1), len(name2)

        if len1 == 0 or len2 == 0:
            return 0.0

        # Levenshtein distance
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if name1[i - 1] == name2[j - 1] else 1
                matrix[i][j] = min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + cost,
                )

        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        return 1.0 - (distance / max_len)

    def find_duplicates(self, records: List[Dict], threshold: float = 0.85) -> List[List[Dict]]:
        """Find duplicate groups using fuzzy matching."""
        groups: Dict[str, List[Dict]] = {}

        for record in records:
            fp = self.generate_fingerprint(record)

            # Try to match with existing groups
            matched = False
            for group_fp, group_records in groups.items():
                if fp == group_fp:
                    groups[fp].append(record)
                    matched = True
                    break

            if not matched:
                # Check fuzzy similarity
                for group_fp, group_records in groups.items():
                    ref_record = group_records[0]
                    sim = self.calculate_similarity(
                        record.get("name", ""),
                        ref_record.get("name", "")
                    )
                    if sim >= threshold:
                        groups[group_fp].append(record)
                        matched = True
                        break

            if not matched:
                groups[fp] = [record]

        # Return only groups with duplicates
        return [records for records in groups.values() if len(records) > 1]

    def deduplicate(
        self, records: List[Dict], merge_strategy: str = "best_score"
    ) -> List[Dict]:
        """
        Deduplicate records with intelligent merging.
        merge_strategy: 'best_score', 'most_complete', 'newest'
        """
        fingerprints: Dict[str, Dict] = {}

        for record in records:
            fp = self.generate_fingerprint(record)

            if fp not in fingerprints:
                fingerprints[fp] = record
            else:
                existing = fingerprints[fp]
                merged = self._merge_records(existing, record, merge_strategy)
                fingerprints[fp] = merged

        return list(fingerprints.values())

    def _merge_records(
        self, record1: Dict, record2: Dict, strategy: str
    ) -> Dict:
        """Merge two records based on strategy."""
        merged = record1.copy()

        for key, value in record2.items():
            if key in merged:
                # Choose which value to keep
                if strategy == "best_score":
                    score1 = record1.get("verification_score", 0)
                    score2 = record2.get("verification_score", 0)
                    if score2 > score1:
                        merged[key] = value
                elif strategy == "most_complete":
                    if value and (not merged.get(key) or len(str(value)) > len(str(merged.get(key)))):
                        merged[key] = value
                elif strategy == "newest":
                    date1 = record1.get("scraped_at", "")
                    date2 = record2.get("scraped_at", "")
                    if date2 > date1:
                        merged[key] = value
            else:
                merged[key] = value

        # Track merge history
        if "merged_sources" not in merged:
            sources = set()
            if isinstance(merged.get("source"), str):
                sources.add(merged["source"])
            if isinstance(record1.get("source"), str):
                sources.add(record1["source"])
            if isinstance(record2.get("source"), str):
                sources.add(record2["source"])
            merged["merged_sources"] = list(sources)

        return merged


class EnhancedValidationPipeline:
    """
    Complete validation pipeline with all validators.
    """

    def __init__(self):
        self.email_validator = EnhancedEmailValidator()
        self.phone_validator = EnhancedPhoneValidator()
        self.address_validator = AddressValidator()
        self.deduplicator = EnhancedDeduplicator()

    def validate_record(self, record: Dict) -> Tuple[bool, Dict, List[str]]:
        """
        Validate a single record.
        Returns (is_valid, cleaned_record, warnings).
        """
        warnings = []
        cleaned = {}

        # Validate name
        if not record.get("name"):
            return False, {}, ["Name is required"]
        cleaned["name"] = record["name"].strip()
        if len(cleaned["name"]) < 2:
            warnings.append("Name is very short")

        # Validate email
        email_result = self.email_validator.validate(record.get("email"))
        if not email_result.is_valid:
            warnings.extend(email_result.errors)
        cleaned["email"] = email_result.cleaned_value

        # Validate phone
        phone_result = self.phone_validator.validate(record.get("phone"))
        if not phone_result.is_valid:
            warnings.extend(phone_result.errors)
        cleaned["phone"] = phone_result.cleaned_value

        # Validate address
        if record.get("address"):
            addr_result = self.address_validator.validate(record["address"])
            if addr_result.is_valid:
                cleaned["address"] = addr_result.cleaned_value
            else:
                warnings.extend(addr_result.errors)

        # Set defaults
        cleaned["contact_json"] = {
            "email": cleaned.get("email"),
            "phone": cleaned.get("phone"),
            "linkedin": record.get("linkedin"),
        }

        cleaned["source"] = record.get("source", "unknown")
        cleaned["verification_score"] = self._calculate_verification_score(cleaned)
        cleaned["scraped_at"] = record.get("scraped_at", datetime.utcnow().isoformat())

        # Overall validation
        is_valid = bool(cleaned.get("name"))

        return is_valid, cleaned, warnings

    def _calculate_verification_score(self, record: Dict) -> float:
        """Calculate verification score based on data quality."""
        score = 0.0

        # Name present (required)
        if record.get("name"):
            score += 0.2

        # Email valid
        if record.get("email"):
            score += 0.25

        # Phone valid
        if record.get("phone"):
            score += 0.15

        # Address present
        if record.get("address"):
            score += 0.15

        # Source known
        if record.get("source") and record["source"] != "unknown":
            score += 0.15

        # Has website
        if record.get("website"):
            score += 0.1

        return min(1.0, score)

    async def process_batch(
        self, records: List[Dict], deduplicate: bool = True
    ) -> Dict:
        """
        Process a batch of records.
        """
        valid_records = []
        invalid_records = []
        all_warnings = []

        # Validate each record
        for i, record in enumerate(records):
            is_valid, cleaned, warnings = self.validate_record(record)
            if is_valid:
                cleaned["_original_index"] = i
                valid_records.append(cleaned)
                if warnings:
                    all_warnings.append({
                        "index": i,
                        "warnings": warnings,
                    })
            else:
                invalid_records.append({
                    "index": i,
                    "original": record,
                })

        # Deduplicate
        deduplication_info = {}
        if deduplicate and valid_records:
            unique_records = self.deduplicator.deduplicate(valid_records)
            deduplication_info = {
                "input_count": len(valid_records),
                "output_count": len(unique_records),
                "duplicates_removed": len(valid_records) - len(unique_records),
            }
        else:
            unique_records = valid_records

        return {
            "valid_records": unique_records,
            "invalid_records": invalid_records,
            "warnings": all_warnings,
            "deduplication_info": deduplication_info,
            "statistics": {
                "total_input": len(records),
                "valid_count": len(unique_records),
                "invalid_count": len(invalid_records),
                "deduplication_ratio": round(
                    len(unique_records) / len(records), 2
                ) if records else 0,
            },
        }


# Convenience functions
async def validate_and_clean(records: List[Dict]) -> Dict:
    """Validate and clean a list of records."""
    pipeline = EnhancedValidationPipeline()
    return await pipeline.process_batch(records)


def deduplicate_records(records: List[Dict]) -> List[Dict]:
    """Deduplicate a list of records."""
    deduplicator = EnhancedDeduplicator()
    return deduplicator.deduplicate(records)
