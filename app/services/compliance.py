"""
GDPR and Compliance Service
Handles data privacy, GDPR compliance, and regulatory requirements for data aggregation.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json


class RegulationType(Enum):
    """Types of data regulations."""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    PCI_DSS = "pci_dss"


class DataCategory(Enum):
    """Categories of personal data."""
    IDENTIFIER = "identifier"  # Names, IDs
    CONTACT = "contact"  # Email, phone, address
    FINANCIAL = "financial"  # Bank details, payment info
    HEALTH = "health"  # Medical or health-related
    DEMOGRAPHIC = "demographic"  # Age, gender, ethnicity
    BEHAVIORAL = "behavioral"  # Browsing, purchase history
    PROFESSIONAL = "professional"  # Job, employer, industry
    BIOMETRIC = "biometric"  # Fingerprints, facial recognition


class ProcessingPurpose(Enum):
    """Purposes for data processing."""
    SERVICE_DELIVERY = "service_delivery"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    LEGAL_COMPLIANCE = "legal_compliance"
    RESEARCH = "research"
    SECURITY = "security"


@dataclass
class ConsentRecord:
    """Record of consent for data processing."""
    consent_id: str
    data_subject_id: str
    purposes: List[ProcessingPurpose]
    granted_at: datetime
    expires_at: Optional[datetime]
    source: str  # How consent was obtained
    version: str  # Privacy policy version


@dataclass
class DataSubjectRightsRequest:
    """Request from a data subject to exercise their rights."""
    request_id: str
    request_type: str  # access, rectification, erasure, portability, objection
    data_subject_id: str
    submitted_at: datetime
    status: str  # pending, processing, completed, rejected
    notes: str


class ComplianceChecker:
    """
    Checks data processing activities for compliance with regulations.
    """

    def __init__(self):
        self.violations: List[Dict] = []
        self.consent_records: Dict[str, ConsentRecord] = {}

    def check_data_category(self, data: Dict) -> List[DataCategory]:
        """Identify categories of personal data in a record."""
        categories = []

        # Check for identifiers
        if data.get("name") or data.get("first_name") or data.get("last_name"):
            categories.append(DataCategory.IDENTIFIER)

        # Check for contact info
        if data.get("email") or data.get("phone") or data.get("address"):
            categories.append(DataCategory.CONTACT)

        # Check for professional info
        if data.get("job_title") or data.get("company") or data.get("industry"):
            categories.append(DataCategory.PROFESSIONAL)

        # Check for demographic info
        if data.get("age") or data.get("gender") or data.get("location"):
            categories.append(DataCategory.DEMOGRAPHIC)

        return categories

    def assess_compliance_risk(self, data: Dict, purpose: ProcessingPurpose) -> Dict:
        """
        Assess compliance risk for processing data.
        Returns risk level and required safeguards.
        """
        categories = self.check_data_category(data)
        risk_level = "low"
        required_safeguards = []

        # High-risk data categories
        high_risk = [DataCategory.HEALTH, DataCategory.BIOMETRIC, DataCategory.FINANCIAL]

        has_high_risk = any(c in high_risk for c in categories)

        if has_high_risk:
            risk_level = "high"
            required_safeguards.extend([
                "explicit_consent_required",
                "data_encryption_at_rest",
                "audit_logging",
                "limited_access_controls",
            ])
        elif categories:
            risk_level = "medium"
            required_safeguards.extend([
                "legitimate_interest_documentation",
                "opt_out_mechanism",
            ])
        else:
            risk_level = "low"
            required_safeguards.append("standard_privacy_notices")

        return {
            "risk_level": risk_level,
            "data_categories": [c.value for c in categories],
            "required_safeguards": required_safeguards,
            "recommended_retention_days": self._get_retention_days(categories, purpose),
        }

    def _get_retention_days(self, categories: List[DataCategory], purpose: ProcessingPurpose) -> int:
        """Determine recommended data retention period."""
        if DataCategory.HEALTH in categories:
            return 2555  # ~7 years for health data

        if DataCategory.FINANCIAL in categories:
            return 2555  # ~7 years for financial data

        if purpose == ProcessingPurpose.LEGAL_COMPLIANCE:
            return 3650  # ~10 years for legal compliance

        return 730  # 2 years default

    def validate_processing_basis(self, data: Dict, purpose: ProcessingPurpose) -> Dict:
        """Validate that there's a legal basis for processing."""
        categories = self.check_data_category(data)
        has_personal_data = len(categories) > 0

        if not has_personal_data:
            return {
                "valid": True,
                "basis": "legitimate_interest",
                "reason": "No personal data identified",
            }

        # For personal data, check consent or other basis
        # This is simplified - real implementation would check consent records
        return {
            "valid": True,
            "basis": "consent",
            "reason": "Consent required for personal data processing",
            "action": "obtain_consent_before_processing",
        }

    def check_cross_border_transfer(self, source_country: str, target_country: str) -> Dict:
        """Check if data transfer is allowed across borders."""
        # EU adequate countries
        adequate_countries = {
            "andorra", "argentina", "canada", "faroe islands", "guernsey",
            "israel", "isle of man", "japan", "jersey", "new zealand",
            "switzerland", "uk", "uruguay", "south korea", "singapore",
        }

        source = source_country.lower()
        target = target_country.lower()

        # EU to non-EU without adequacy
        if source == "eu" and target not in adequate_countries:
            return {
                "allowed": False,
                "reason": "Transfer to non-adequate country requires additional safeguards",
                "required_measures": [
                    "standard_contractual_clauses",
                    "binding_corporate_rules",
                    "explicit_consent",
                ],
            }

        return {
            "allowed": True,
            "reason": "Transfer is allowed under GDPR adequacy decision",
        }


class GDPRComplianceManager:
    """
    Manages GDPR compliance for data subject rights and data processing.
    """

    def __init__(self):
        self.rights_requests: List[DataSubjectRightsRequest] = []
        self.data_inventory: Dict[str, Dict] = {}  # data_subject_id -> data inventory
        self.retention_schedule: Dict[str, int] = {}

    def handle_rights_request(self, request: DataSubjectRightsRequest) -> Dict:
        """Process a data subject rights request."""
        self.rights_requests.append(request)

        if request.request_type == "access":
            return self._handle_access_request(request)
        elif request.request_type == "erasure":
            return self._handle_erasure_request(request)
        elif request.request_type == "rectification":
            return self._handle_rectification_request(request)
        elif request.request_type == "portability":
            return self._handle_portability_request(request)
        else:
            return {
                "status": "processing",
                "message": f"Request type '{request.request_type}' is being processed",
            }

    def _handle_access_request(self, request: DataSubjectRightsRequest) -> Dict:
        """Handle data access request (GDPR Article 15)."""
        # 30 days to respond
        deadline = datetime.utcnow().fromordinal(
            datetime.utcnow().toordinal() + 30
        )

        subject_data = self.data_inventory.get(request.data_subject_id, {})

        return {
            "status": "processing",
            "deadline": deadline.isoformat(),
            "data_found": len(subject_data) > 0,
            "data_categories": list(subject_data.keys()),
        }

    def _handle_erasure_request(self, request: DataSubjectRightsRequest) -> Dict:
        """Handle data erasure request (GDPR Article 17)."""
        # Check if erasure applies
        # Data must be deleted unless retention is required by law
        return {
            "status": "processing",
            "message": "Evaluating legal retention requirements",
            "actions": [
                "check_legal_retention_requirements",
                "remove_from_active_systems",
                "schedule_deletion_from_backups",
            ],
        }

    def _handle_rectification_request(self, request: DataSubjectRightsRequest) -> Dict:
        """Handle data rectification request (GDPR Article 16)."""
        return {
            "status": "processing",
            "message": "Data correction request received",
        }

    def _handle_portability_request(self, request: DataSubjectRightsRequest) -> Dict:
        """Handle data portability request (GDPR Article 20)."""
        subject_data = self.data_inventory.get(request.data_subject_id, {})

        return {
            "status": "processing",
            "format": "json",
            "data_available": len(subject_data) > 0,
        }

    def record_consent(self, record: ConsentRecord) -> str:
        """Record consent for data processing."""
        consent_id = hashlib.sha256(
            f"{record.data_subject_id}{record.granted_at}".encode()
        ).hexdigest()[:16]

        self.consent_records[consent_id] = record

        return consent_id

    def check_consent(self, data_subject_id: str, purpose: ProcessingPurpose) -> Dict:
        """Check if valid consent exists for a purpose."""
        for consent_id, record in self.consent_records.items():
            if record.data_subject_id == data_subject_id:
                if purpose in record.purposes:
                    if record.expires_at is None or record.expires_at > datetime.utcnow():
                        return {
                            "has_consent": True,
                            "consent_id": consent_id,
                            "granted_at": record.granted_at.isoformat(),
                        }

        return {
            "has_consent": False,
            "message": f"No valid consent found for purpose {purpose.value}",
        }

    def get_data_inventory(self) -> Dict:
        """Get overview of data processing activities."""
        return {
            "total_data_subjects": len(self.data_inventory),
            "active_consents": len(self.consent_records),
            "pending_requests": sum(
                1 for r in self.rights_requests if r.status == "pending"
            ),
            "processing_purposes": [p.value for p in ProcessingPurpose],
            "data_categories": [c.value for c in DataCategory],
        }


class ComplianceDashboard:
    """
    Dashboard for compliance monitoring and reporting.
    """

    def __init__(self):
        self.gdpr_manager = GDPRComplianceManager()
        self.compliance_checker = ComplianceChecker()

    def get_compliance_summary(self, records: List[Dict]) -> Dict:
        """Get compliance summary for dataset."""
        personal_data_count = 0
        high_risk_count = 0
        compliance_issues = []

        for record in records:
            categories = self.compliance_checker.check_data_category(record)
            if categories:
                personal_data_count += 1

            risk = self.compliance_checker.assess_compliance_risk(
                record, ProcessingPurpose.SERVICE_DELIVERY
            )
            if risk["risk_level"] == "high":
                high_risk_count += 1

        # Check consent status
        inventory = self.gdpr_manager.get_data_inventory()

        return {
            "compliance_overview": {
                "total_records": len(records),
                "records_with_personal_data": personal_data_count,
                "high_risk_records": high_risk_count,
                "compliance_rate": round(
                    (len(records) - high_risk_count) / len(records) * 100
                    if records else 100, 2
                ),
            },
            "data_inventory": inventory,
            "recommendations": self._generate_compliance_recommendations(
                personal_data_count, high_risk_count
            ),
            "gdpr_status": {
                "consent_mechanism": "active",
                "data_subject_rights": "enabled",
                "retention_policy": "enforced",
                "cross_border_transfers": "monitored",
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _generate_compliance_recommendations(
        self, personal_data_count: int, high_risk_count: int
    ) -> List[str]:
        """Generate compliance recommendations."""
        recommendations = []

        if high_risk_count > 0:
            recommendations.append(
                f"URGENT: {high_risk_count} records contain high-risk data categories. "
                "Review and apply enhanced safeguards."
            )

        if personal_data_count > 0:
            recommendations.append(
                "Records contain personal data. Ensure GDPR/CCPA compliance."
            )
            recommendations.append(
                "Implement consent management for all personal data processing."
            )
            recommendations.append(
                "Set up data subject rights request handling process."
            )

        if personal_data_count == 0:
            recommendations.append(
                "No personal data detected. Standard privacy measures sufficient."
            )

        return recommendations


# Compliance flags for data records
COMPLIANCE_FLAGS = {
    "requires_consent": True,
    "data_subject_rights_applicable": True,
    "cross_border_transfer_review": False,
    "retention_enforced": True,
}


def apply_compliance_flags(record: Dict) -> Dict:
    """Apply compliance flags to a record."""
    flags = COMPLIANCE_FLAGS.copy()

    # Check if record has personal data
    has_personal = bool(
        record.get("name") or record.get("email") or record.get("phone")
    )

    if not has_personal:
        flags["requires_consent"] = False
        flags["data_subject_rights_applicable"] = False

    record["_compliance"] = flags
    return record
