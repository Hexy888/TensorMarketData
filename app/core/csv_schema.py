"""
CSV Schema Validation for Lead Deliverables
"""
from typing import Dict, List, Optional, Tuple
from enum import Enum
import csv
import io

class Package(str, Enum):
    STARTER = "starter"
    PRO = "pro"
    PREMIUM = "premium"

# Column schemas
STARTER_SCHEMA = [
    "first_name",
    "last_name", 
    "title",
    "verified_work_email",
    "company_name",
    "domain",
    "industry_broad",
    "employee_range_broad"
]

PRO_SCHEMA = [
    "first_name",
    "last_name",
    "title", 
    "verified_work_email",
    "linkedin_url",
    "company_name",
    "domain",
    "industry_specific",
    "employee_range",
    "hq_location"
]

PREMIUM_SCHEMA = PRO_SCHEMA + [
    "targeting_notes",
    "trigger_type",
    "trigger_detail",
    "exclusions_applied"
]

# Optional columns for Pro/Premium
OPTIONAL_COLUMNS = [
    "funding_stage_or_round",
    "tech_stack_hint", 
    "recent_news_link"
]

# Allowed values
EMPLOYEE_RANGES = [
    "1-10", "11-50", "51-200", "201-500", 
    "501-1000", "1001-5000", "5001-10000", "10000+"
]

def validate_csv_schema(csv_content: str, package: Package) -> Tuple[bool, List[str]]:
    """
    Validate CSV against package schema.
    Returns (is_valid, error_messages)
    """
    errors = []
    
    # Parse CSV
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
    except Exception as e:
        return False, [f"Failed to parse CSV: {str(e)}"]
    
    if not rows:
        return False, ["CSV is empty"]
    
    # Get expected columns
    if package == Package.STARTER:
        required_cols = STARTER_SCHEMA
    elif package == Package.PRO:
        required_cols = PRO_SCHEMA
    else:
        required_cols = PREMIUM_SCHEMA
    
    # Check headers
    actual_cols = rows[0].keys()
    missing_cols = [c for c in required_cols if c not in actual_cols]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Check for extra columns (warn only)
    extra_cols = [c for c in actual_cols if c not in required_cols and c not in OPTIONAL_COLUMNS]
    if extra_cols:
        errors.append(f"Unexpected columns (will be ignored): {', '.join(extra_cols)}")
    
    # Validate rows
    for i, row in enumerate(rows, start=2):
        # Required fields
        for col in required_cols[:6]:  # Core contact fields
            if not row.get(col, "").strip():
                errors.append(f"Row {i}: Missing required field '{col}'")
        
        # Email format
        email = row.get("verified_work_email", "").strip()
        if email and "@" not in email:
            errors.append(f"Row {i}: Invalid email format '{email}'")
        elif email:
            # Check lowercase
            if email != email.lower():
                errors.append(f"Row {i}: Email should be lowercase '{email}'")
        
        # Domain format
        domain = row.get("domain", "").strip()
        if domain and (domain.startswith("http://") or domain.startswith("https://")):
            errors.append(f"Row {i}: Domain should not include protocol '{domain}'")
        
        # Employee range validation
        emp_range = row.get("employee_range", row.get("employee_range_broad", "")).strip()
        if emp_range and emp_range not in EMPLOYEE_RANGES:
            errors.append(f"Row {i}: Invalid employee_range '{emp_range}'. Use: {', '.join(EMPLOYEE_RANGES)}")
    
    return len(errors) == 0, errors

def get_schema_columns(package: Package) -> List[str]:
    """Get list of columns for a package."""
    if package == Package.STARTER:
        return STARTER_SCHEMA
    elif package == Package.PRO:
        return PRO_SCHEMA
    return PREMIUM_SCHEMA

def generate_csv_template(package: Package) -> str:
    """Generate a CSV template for a package."""
    columns = get_schema_columns(package)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    return output.getvalue()

def validate_row_count(csv_content: str, expected_count: int) -> Tuple[bool, str]:
    """Validate row count matches order quantity."""
    reader = csv.DictReader(io.StringIO(csv_content))
    row_count = sum(1 for _ in reader)
    
    if row_count < expected_count:
        return False, f"Expected {expected_count} rows, found {row_count}"
    return True, f"Found {row_count} rows (expected {expected_count})"
