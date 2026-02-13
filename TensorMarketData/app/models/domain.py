"""
SQLAlchemy domain models for TensorMarketData.
Tables: suppliers, products, api_keys
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Supplier(Base):
    """
    Suppliers table - stores business data with vector embeddings.
    """

    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, index=True)
    industry_vector = Column(JSON, nullable=True)  # Stores embedding as array
    contact_json = Column(JSON, nullable=False)  # Strict schema: {email, phone, linkedin}
    verification_score = Column(Float, default=0.0, nullable=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to products
    products = relationship("Product", back_populates="supplier", lazy="dynamic")


class Product(Base):
    """
    Products table - inventory and pricing linked to suppliers.
    """

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    supplier_id = Column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku_data = Column(JSON, nullable=False)  # Product identification data
    price_range = Column(JSON, nullable=False)  # {min, max, currency}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to supplier
    supplier = relationship("Supplier", back_populates="products")


class APIKey(Base):
    """
    API Keys table - for authentication and credit tracking.
    """

    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(8), nullable=False)  # For display (e.g., "tmd_live_xxx")
    credits_remaining = Column(Integer, default=100, nullable=False)
    is_active = Column(Integer, default=1, nullable=False)  # 1=active, 0=revoked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
