"""
Data ingestion service.
Handles CSV parsing, validation, and enrichment.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

import pandas as pd
from pydantic import ValidationError

from app.core.config import settings
from app.models.domain import Supplier, Product
from app.models.schemas import (
    ContactData,
    SupplierCreate,
    ProductCreate,
    PriceRange,
    SKUData,
)


class IngestionService:
    """
    Service for ingesting and validating data from various sources.
    """

    def __init__(self):
        self.stats = {
            "processed": 0,
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }

    def reset_stats(self) -> None:
        """Reset ingestion statistics."""
        self.stats = {
            "processed": 0,
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get current ingestion statistics."""
        return self.stats

    def validate_contact(self, contact_data: Dict[str, Any]) -> Optional[ContactData]:
        """
        Validate and normalize contact data.
        Returns None if validation fails.
        """
        try:
            return ContactData(**contact_data)
        except ValidationError as e:
            self.stats["errors"].append(f"Contact validation error: {e}")
            return None

    def validate_supplier(self, row: Dict[str, Any]) -> Optional[SupplierCreate]:
        """
        Validate a single supplier row from CSV.
        Returns None if validation fails.
        """
        try:
            # Extract contact from row
            contact = {
                "email": row.get("email"),
                "phone": row.get("phone"),
                "linkedin": row.get("linkedin"),
            }

            # Validate contact
            validated_contact = self.validate_contact(contact)
            if not validated_contact:
                self.stats["invalid"] += 1
                return None

            return SupplierCreate(
                name=row.get("name", "").strip(),
                contact=validated_contact,
                verification_score=float(row.get("verification_score", 0.0)),
            )
        except Exception as e:
            self.stats["errors"].append(f"Supplier error: {e}")
            self.stats["invalid"] += 1
            return None

    def validate_product(self, row: Dict[str, Any], supplier_id: uuid4) -> Optional[ProductCreate]:
        """
        Validate a single product row from CSV.
        Returns None if validation fails.
        """
        try:
            price_range = PriceRange(
                min=float(row.get("price_min", 0)),
                max=float(row.get("price_max", 0)),
                currency=row.get("currency", "USD"),
            )

            sku = SKUData(
                sku=row.get("sku", "").strip(),
                name=row.get("product_name"),
                category=row.get("category"),
                attributes={
                    "description": row.get("description"),
                    "tags": row.get("tags", "").split(",") if row.get("tags") else None,
                },
            )

            return ProductCreate(
                supplier_id=supplier_id,
                sku=sku.sku,
                price_range=price_range,
                attributes=sku.attributes,
            )
        except Exception as e:
            self.stats["errors"].append(f"Product error: {e}")
            self.stats["invalid"] += 1
            return None

    async def process_csv(
        self,
        file_path: str,
        supplier_mapping: Dict[str, uuid4],
    ) -> Dict[str, Any]:
        """
        Process a CSV file and ingest suppliers and products.

        Args:
            file_path: Path to CSV file
            supplier_mapping: Mapping of supplier names to IDs

        Returns:
            Ingestion statistics
        """
        self.reset_stats()

        # Read CSV
        df = pd.read_csv(file_path)

        # Determine if this is suppliers or products CSV
        if "email" in df.columns or "phone" in df.columns:
            # Suppliers CSV
            for _, row in df.iterrows():
                self.stats["processed"] += 1
                validated = self.validate_supplier(row.to_dict())
                if validated:
                    self.stats["valid"] += 1
                else:
                    self.stats["invalid"] += 1
        elif "sku" in df.columns or "price_min" in df.columns:
            # Products CSV
            for _, row in df.iterrows():
                supplier_name = row.get("supplier_name")
                if supplier_name and supplier_name in supplier_mapping:
                    self.stats["processed"] += 1
                    validated = self.validate_product(
                        row.to_dict(), supplier_mapping[supplier_name]
                    )
                    if validated:
                        self.stats["valid"] += 1
                    else:
                        self.stats["invalid"] += 1

        return self.stats


class DataCleaner:
    """
    Utility class for data cleaning operations.
    """

    @staticmethod
    def clean_email(email: Optional[str]) -> Optional[str]:
        """Normalize email address."""
        if not email:
            return None
        return email.strip().lower()

    @staticmethod
    def clean_phone(phone: Optional[str]) -> Optional[str]:
        """Normalize phone number."""
        if not phone:
            return None
        # Remove all non-numeric characters except +
        import re
        cleaned = re.sub(r"[^\d+]", "", phone.strip())
        return cleaned if cleaned else None

    @staticmethod
    def clean_url(url: Optional[str]) -> Optional[str]:
        """Normalize URL."""
        if not url:
            return None
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    @staticmethod
    def validate_not_empty(value: Any) -> bool:
        """Check if value is not empty."""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        return True
