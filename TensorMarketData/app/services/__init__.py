"""
Services Package
"""

from app.services.collection.scraper import (
    BaseScraper,
    DataCollector,
    SECScraper,
    FDAScraper,
    LinkedInScraper,
    DirectoryScraper,
    collect_from_apis,
    collect_from_directory,
)

from app.services.collection.enhanced_scraper import (
    EnhancedBaseScraper,
    BetterBusinessBureauScraper,
    CrunchbaseScraper,
    OpenCorporatesScraper,
    LinkedInSalesNavigatorScraper,
    YellowPagesScraper,
    MantaScraper,
    IndustryAssociationScraper,
    GovernmentContractorScraper,
    EDGARScraper,
    DataCollector,
    create_default_collector,
)

from app.services.validation.cleaner import (
    DataValidator,
    Deduplicator,
    DataEnricher,
    process_data,
)

from app.services.validation.enhanced_cleaner import (
    EnhancedEmailValidator,
    EnhancedPhoneValidator,
    AddressValidator,
    CompanyNameNormalizer,
    EnhancedDeduplicator,
    EnhancedValidationPipeline,
    validate_and_clean,
    deduplicate_records,
)

from app.services.enrichment import (
    CompanyAPIClient,
    SocialSignalsEnricher,
    NewsFeedEnricher,
    DataEnrichmentPipeline,
    enrich_company_data,
    enrich_batch_companies,
)

from app.services.quality_metrics import (
    QualityDimension,
    QualityScore,
    DataQualityMetrics,
    DataQualityDashboard,
)

from app.services.compliance import (
    RegulationType,
    DataCategory,
    ProcessingPurpose,
    ConsentRecord,
    DataSubjectRightsRequest,
    ComplianceChecker,
    GDPRComplianceManager,
    ComplianceDashboard,
    apply_compliance_flags,
)

__all__ = [
    # Original scrapers
    "BaseScraper",
    "DataCollector",
    "SECScraper",
    "FDAScraper",
    "LinkedInScraper",
    "DirectoryScraper",
    "collect_from_apis",
    "collect_from_directory",
    
    # Enhanced scrapers
    "EnhancedBaseScraper",
    "BetterBusinessBureauScraper",
    "CrunchbaseScraper",
    "OpenCorporatesScraper",
    "LinkedInSalesNavigatorScraper",
    "YellowPagesScraper",
    "MantaScraper",
    "IndustryAssociationScraper",
    "GovernmentContractorScraper",
    "EDGARScraper",
    "create_default_collector",
    
    # Original validation
    "DataValidator",
    "Deduplicator",
    "DataEnricher",
    "process_data",
    
    # Enhanced validation
    "EnhancedEmailValidator",
    "EnhancedPhoneValidator",
    "AddressValidator",
    "CompanyNameNormalizer",
    "EnhancedDeduplicator",
    "EnhancedValidationPipeline",
    "validate_and_clean",
    "deduplicate_records",
    
    # Enrichment
    "CompanyAPIClient",
    "SocialSignalsEnricher",
    "NewsFeedEnricher",
    "DataEnrichmentPipeline",
    "enrich_company_data",
    "enrich_batch_companies",
    
    # Quality metrics
    "QualityDimension",
    "QualityScore",
    "DataQualityMetrics",
    "DataQualityDashboard",
    
    # Compliance
    "RegulationType",
    "DataCategory",
    "ProcessingPurpose",
    "ConsentRecord",
    "DataSubjectRightsRequest",
    "ComplianceChecker",
    "GDPRComplianceManager",
    "ComplianceDashboard",
    "apply_compliance_flags",
]
