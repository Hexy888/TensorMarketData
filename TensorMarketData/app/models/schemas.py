"""
Pydantic schemas for request/response validation.
Strict typing - data must conform or be rejected.
"""

from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ==================== Contact Schema ====================

class ContactData(BaseModel):
    """
    Strict contact information schema.
    All fields optional but validated if present.
    """

    email: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: Optional[str] = Field(None, max_length=20)
    linkedin: Optional[str] = Field(None, max_length=500)


# ==================== Supplier Schemas ====================

class SupplierCreate(BaseModel):
    """
    Schema for creating a supplier.
    """

    name: str = Field(..., min_length=1, max_length=255)
    contact: ContactData
    verification_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SupplierResponse(BaseModel):
    """
    Schema for supplier data in responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    industry_vector: Optional[List[float]] = None
    contact: ContactData
    verification_score: float
    last_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class SupplierWithProducts(SupplierResponse):
    """
    Supplier with nested products.
    """

    products: List["ProductResponse"] = []


# ==================== Product Schemas ====================

class PriceRange(BaseModel):
    """
    Price range schema.
    """

    min: float = Field(..., ge=0.0)
    max: float = Field(..., ge=0.0)
    currency: str = Field(default="USD", max_length=3)


class SKUData(BaseModel):
    """
    SKU data schema - flexible for different product types.
    """

    sku: str
    name: Optional[str] = None
    category: Optional[str] = None
    attributes: Optional[dict[str, Any]] = None


class ProductCreate(BaseModel):
    """
    Schema for creating a product.
    """

    supplier_id: UUID
    sku: str
    price_range: PriceRange
    attributes: Optional[dict[str, Any]] = None


class ProductResponse(BaseModel):
    """
    Schema for product data in responses.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    supplier_id: UUID
    sku: SKUData
    price_range: PriceRange
    created_at: datetime
    updated_at: datetime


# ==================== API Key Schemas ====================

class APIKeyCreate(BaseModel):
    """
    Schema for creating an API key.
    """

    credits: int = Field(default=100, ge=1)
    expires_days: Optional[int] = Field(None, ge=1)


class APIKeyResponse(BaseModel):
    """
    Schema for API key in responses.
    Note: Full key shown only on creation.
    """

    id: UUID
    key_prefix: str
    credits_remaining: int
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class APIKeyCreated(BaseModel):
    """
    Response when API key is first created - includes full key.
    """

    id: UUID
    key: str  # Full key - only shown once!
    key_prefix: str
    credits_remaining: int
    created_at: datetime


# ==================== Search Schemas ====================

class SearchQuery(BaseModel):
    """
    Natural language search query.
    """

    q: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    """
    Individual search result.
    """

    supplier: SupplierResponse
    score: float
    products: List[ProductResponse] = []


class SearchResponse(BaseModel):
    """
    Search response with results and metadata.
    """

    query: str
    total_results: int
    results: List[SearchResult]
    credits_used: int
    credits_remaining: int


# ==================== Inventory Schema ====================

class InventoryResponse(BaseModel):
    """
    Inventory data for a supplier.
    """

    supplier_id: UUID
    supplier_name: str
    products: List[ProductResponse]
    total_products: int


# ==================== Error Schema ====================

class ErrorResponse(BaseModel):
    """
    Standard error response.
    """

    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ==================== Health Schema ====================

class HealthResponse(BaseModel):
    """
    Health check response.
    """

    status: str
    version: str
    database: str


# Update forward references
SupplierResponse.model_rebuild()
SupplierWithProducts.model_rebuild()
