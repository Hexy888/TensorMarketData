"""
Data Quality Metrics Service
Tracks and reports on data quality metrics for supplier records.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class QualityDimension(Enum):
    """Data quality dimensions."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"


@dataclass
class QualityScore:
    """Quality score for a record or dataset."""
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    timeliness_score: float
    validity_score: float
    uniqueness_score: float
    calculated_at: str
    issues: List[str]
    suggestions: List[str]


class DataQualityMetrics:
    """
    Calculates and tracks data quality metrics for supplier data.
    """

    # Field importance weights
    FIELD_WEIGHTS = {
        "name": 1.0,
        "email": 0.8,
        "phone": 0.6,
        "website": 0.5,
        "linkedin": 0.4,
        "address": 0.5,
        "industry": 0.6,
        "size_estimate": 0.4,
        "verification_score": 0.7,
    }

    def __init__(self):
        self.metrics_history: List[Dict] = []

    def calculate_completeness(self, record: Dict) -> float:
        """Calculate completeness score (0-1) based on filled fields."""
        if not record:
            return 0.0

        total_weight = 0.0
        filled_weight = 0.0

        for field, weight in self.FIELD_WEIGHTS.items():
            total_weight += weight
            # Check various possible field locations
            value = record.get(field)
            if not value:
                value = record.get("contact_json", {}).get(field)
            if value:
                filled_weight += weight

        return filled_weight / total_weight if total_weight > 0 else 0.0

    def calculate_accuracy(self, record: Dict) -> float:
        """Calculate accuracy score based on data validation."""
        score = 0.5  # Base score

        # Email validation
        email = record.get("email") or record.get("contact_json", {}).get("email")
        if email and self._is_valid_email(email):
            score += 0.1

        # Phone validation
        phone = record.get("phone") or record.get("contact_json", {}).get("phone")
        if phone and self._is_valid_phone(phone):
            score += 0.1

        # Website validation
        website = record.get("website") or record.get("linkedin")
        if website and self._is_valid_url(website):
            score += 0.1

        # Name looks reasonable
        name = record.get("name", "")
        if len(name) >= 2 and len(name) <= 200:
            score += 0.1

        # Verification score correlation
        v_score = record.get("verification_score", 0.5)
        if v_score >= 0.7:
            score += 0.1

        return min(1.0, score)

    def _is_valid_email(self, email: str) -> bool:
        import re
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, str(email))) if email else False

    def _is_valid_phone(self, phone: str) -> bool:
        import re
        if not phone:
            return False
        cleaned = re.sub(r"[^\d\+]", "", str(phone))
        return 7 <= len(cleaned) <= 15

    def _is_valid_url(self, url: str) -> bool:
        if not url:
            return False
        url = str(url)
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return bool(result.netloc)
        except Exception:
            return False

    def calculate_consistency(self, record: Dict, related_records: List[Dict] = None) -> float:
        """Calculate consistency score."""
        # Check internal consistency
        score = 1.0

        # Name and industry mismatch
        name = record.get("name", "").lower()
        industry = record.get("industry", "").lower()

        # High-value indicators in name but low-value industry
        high_value_words = ["enterprise", "global", "international"]
        low_value_industries = ["other", "unknown"]

        if any(word in name for word in high_value_words):
            if industry in low_value_industries:
                score -= 0.2

        return max(0.0, min(1.0, score))

    def calculate_timeliness(self, record: Dict) -> float:
        """Calculate timeliness score based on when data was collected."""
        from datetime import datetime

        scraped_at = record.get("scraped_at")
        if not scraped_at:
            return 0.5

        try:
            # Parse ISO format
            if isinstance(scraped_at, str):
                scraped_date = datetime.fromisoformat(scraped_at.replace("Z", "+00:00"))
            else:
                scraped_date = datetime.utcnow()

            days_ago = (datetime.utcnow() - scraped_date).days

            if days_ago <= 7:
                return 1.0
            elif days_ago <= 30:
                return 0.9
            elif days_ago <= 90:
                return 0.7
            elif days_ago <= 180:
                return 0.5
            elif days_ago <= 365:
                return 0.3
            else:
                return 0.1
        except Exception:
            return 0.5

    def calculate_validity(self, record: Dict) -> float:
        """Calculate validity score based on data format compliance."""
        score = 1.0

        # Name validity
        name = record.get("name", "")
        if not name or len(name) < 2:
            score -= 0.3
        elif len(name) > 200:
            score -= 0.1

        # Email validity
        email = record.get("email") or record.get("contact_json", {}).get("email")
        if email and not self._is_valid_email(email):
            score -= 0.2

        # Phone validity
        phone = record.get("phone") or record.get("contact_json", {}).get("phone")
        if phone and not self._is_valid_phone(phone):
            score -= 0.2

        # Source validity
        source = record.get("source")
        if not source or source == "unknown":
            score -= 0.2

        return max(0.0, min(1.0, score))

    def calculate_uniqueness(self, record: Dict, all_records: List[Dict] = None) -> float:
        """Calculate uniqueness score (inverse of duplicate likelihood)."""
        if not all_records:
            return 1.0

        name = record.get("name", "").lower().strip()
        email = record.get("email") or record.get("contact_json", {}).get("email", "").lower()

        matches = 0
        for other in all_records:
            if other is record:
                continue

            other_name = other.get("name", "").lower().strip()
            other_email = other.get("email") or other.get("contact_json", {}).get("email", "").lower()

            # Name similarity
            if name and other_name:
                if name == other_name:
                    matches += 1
                elif name in other_name or other_name in name:
                    matches += 0.5

            # Email match
            if email and other_email:
                if email == other_email:
                    matches += 2

        if matches == 0:
            return 1.0
        elif matches == 1:
            return 0.7
        else:
            return max(0.0, 1.0 - (matches * 0.15))

    def calculate_quality_score(self, record: Dict, related_records: List[Dict] = None) -> QualityScore:
        """
        Calculate comprehensive quality score for a record.
        """
        completeness = self.calculate_completeness(record)
        accuracy = self.calculate_accuracy(record)
        consistency = self.calculate_consistency(record, related_records)
        timeliness = self.calculate_timeliness(record)
        validity = self.calculate_validity(record)
        uniqueness = self.calculate_uniqueness(record, related_records)

        # Weighted overall score
        weights = {
            "completeness": 0.25,
            "accuracy": 0.25,
            "consistency": 0.15,
            "timeliness": 0.1,
            "validity": 0.15,
            "uniqueness": 0.1,
        }

        overall = (
            completeness * weights["completeness"] +
            accuracy * weights["accuracy"] +
            consistency * weights["consistency"] +
            timeliness * weights["timeliness"] +
            validity * weights["validity"] +
            uniqueness * weights["uniqueness"]
        )

        # Generate issues and suggestions
        issues = []
        suggestions = []

        if completeness < 0.5:
            issues.append("Low completeness score")
            suggestions.append("Add missing contact information")

        if accuracy < 0.5:
            issues.append("Potential accuracy issues")
            suggestions.append("Verify email and phone formats")

        if validity < 0.5:
            issues.append("Data validity concerns")
            suggestions.append("Review required fields")

        if timeliness < 0.5:
            issues.append("Data may be stale")
            suggestions.append("Re-collect from source")

        if uniqueness < 0.5:
            issues.append("Possible duplicate detected")
            suggestions.append("Review against existing records")

        return QualityScore(
            overall_score=round(overall, 3),
            completeness_score=round(completeness, 3),
            accuracy_score=round(accuracy, 3),
            consistency_score=round(consistency, 3),
            timeliness_score=round(timeliness, 3),
            validity_score=round(validity, 3),
            uniqueness_score=round(uniqueness, 3),
            calculated_at=datetime.utcnow().isoformat(),
            issues=issues,
            suggestions=suggestions,
        )

    def calculate_dataset_quality(self, records: List[Dict]) -> Dict:
        """
        Calculate aggregate quality metrics for a dataset.
        """
        if not records:
            return {
                "total_records": 0,
                "average_quality": 0.0,
                "quality_distribution": {},
                "top_issues": [],
            }

        scores = [self.calculate_quality_score(r, records) for r in records]

        total = len(scores)
        avg_quality = sum(s.overall_score for s in scores) / total

        # Quality distribution
        quality_ranges = {
            "excellent": sum(1 for s in scores if s.overall_score >= 0.8),
            "good": sum(1 for s in scores if 0.6 <= s.overall_score < 0.8),
            "fair": sum(1 for s in scores if 0.4 <= s.overall_score < 0.6),
            "poor": sum(1 for s in scores if s.overall_score < 0.4),
        }

        # Dimension averages
        dimension_avgs = {
            dim.value: round(sum(getattr(s, f"{dim.value}_score") for s in scores) / total, 3)
            for dim in QualityDimension
        }

        # Aggregate issues
        all_issues = {}
        for s in scores:
            for issue in s.issues:
                all_issues[issue] = all_issues.get(issue, 0) + 1

        top_issues = sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_records": total,
            "average_quality": round(avg_quality, 3),
            "quality_distribution": quality_ranges,
            "dimension_averages": dimension_avgs,
            "top_issues": [f"{issue} ({count})" for issue, count in top_issues],
            "calculated_at": datetime.utcnow().isoformat(),
        }


class DataQualityDashboard:
    """
    Dashboard data provider for data quality monitoring.
    """

    def __init__(self):
        self.metrics_service = DataQualityMetrics()

    def get_dashboard_summary(self, records: List[Dict]) -> Dict:
        """Get dashboard summary data."""
        dataset_quality = self.metrics_service.calculate_dataset_quality(records)

        # Quality by source
        by_source: Dict[str, List] = {}
        for record in records:
            source = record.get("source", "unknown")
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(record)

        source_quality = {}
        for source, source_records in by_source.items():
            source_quality[source] = self.metrics_service.calculate_dataset_quality(source_records)

        return {
            "overview": dataset_quality,
            "by_source": source_quality,
            "recommendations": self._generate_recommendations(dataset_quality),
        }

    def _generate_recommendations(self, dataset_quality: Dict) -> List[str]:
        """Generate recommendations based on quality metrics."""
        recommendations = []

        avg_quality = dataset_quality.get("average_quality", 0)

        if avg_quality < 0.5:
            recommendations.append("URGENT: Overall data quality is below acceptable levels")
            recommendations.append("Consider pausing data collection until issues are addressed")

        dimension_avgs = dataset_quality.get("dimension_averages", {})

        if dimension_avgs.get("completeness", 1) < 0.5:
            recommendations.append("Focus on filling missing contact fields")

        if dimension_avgs.get("timeliness", 1) < 0.5:
            recommendations.append("Implement regular data refresh cycles")

        if dimension_avgs.get("uniqueness", 1) < 0.7:
            recommendations.append("Improve deduplication processes")

        total = dataset_quality.get("total_records", 0)
        poor_count = dataset_quality.get("quality_distribution", {}).get("poor", 0)

        if poor_count > total * 0.1:
            recommendations.append(f"Review and potentially remove {poor_count} poor-quality records")

        if not recommendations:
            recommendations.append("Data quality is in good shape! Continue monitoring.")

        return recommendations
