"""
API Endpoints for TensorMarketData.
Handles: /health, /search, /inventory
Uses Supabase REST API for database operations.
"""

from typing import Optional
from uuid import UUID
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.config import settings
from app.core.supabase import supabase, check_health
from app.api.v1.auth import validate_api_key
from app.models.domain import APIKey
from app.models.schemas import (
    SearchResponse,
    SearchResult,
    InventoryResponse,
    ProductResponse,
    SupplierResponse,
    HealthResponse,
    ErrorResponse,
)

# Import data sources
try:
    from app.services.data_sources import SAMPLE_COMPANIES, get_company_info, search_companies
    DATA_SOURCES_AVAILABLE = True
except ImportError:
    DATA_SOURCES_AVAILABLE = False
    SAMPLE_COMPANIES = []

logger = logging.getLogger(__name__)
from app.core.config import settings
from app.core.supabase import supabase, check_health
from app.api.v1.auth import validate_api_key
from app.models.domain import APIKey
from app.models.schemas import (
    SearchResponse,
    SearchResult,
    InventoryResponse,
    ProductResponse,
    SupplierResponse,
    HealthResponse,
    ErrorResponse,
)

router = APIRouter()


# ==================== Health Check ====================

@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check endpoint",
)
async def health_check() -> HealthResponse:
    """
    Returns API status and version.
    Does not require authentication.
    """
    healthy, db_status = await check_health()

    return HealthResponse(
        status="healthy" if healthy else "degraded",
        version="0.1.0",
        database=db_status,
    )


# ==================== Search Endpoint ====================

@router.get(
    "/search",
    response_model=SearchResponse,
    tags=["Data"],
    summary="Vector search for suppliers",
)
async def search_suppliers(
    q: str = Query(..., min_length=1, max_length=500, description="Natural language search query"),
    api_key: APIKey = Depends(validate_api_key),
) -> SearchResponse:
    """
    Search suppliers using natural language query.

    Requires authentication and deducts 1 credit.
    """
    try:
        # Get suppliers matching the query
        suppliers = await supabase.get_suppliers(name_filter=q, limit=10)
        logger.debug(f"Found {len(suppliers)} suppliers for query: {q}")

        # Build search results
        search_results = []
        for s in suppliers:
            logger.debug(f"Processing supplier: {s['name']}")
            # Get products for this supplier
            products = await supabase.get_products_by_supplier(s["id"])

            # Parse contact JSON
            contact = s.get("contact_json", {})

            search_results.append(
                SearchResult(
                    supplier=SupplierResponse(
                        id=s["id"],
                        name=s["name"],
                        industry_vector=s.get("industry_vector"),
                        contact=contact,
                        verification_score=s.get("verification_score", 0.0),
                        last_verified_at=s.get("last_verified_at"),
                        created_at=s["created_at"],
                        updated_at=s["updated_at"],
                    ),
                    score=0.9,  # Mock score for now
                    products=[
                        ProductResponse(
                            id=p["id"],
                            supplier_id=p["supplier_id"],
                            sku=p["sku_data"],
                            price_range=p["price_range"],
                            created_at=p["created_at"],
                            updated_at=p["updated_at"],
                        )
                        for p in products
                    ],
                )
            )

        # Deduct credits (update API key in database)
        new_credits = api_key.credits_remaining - settings.credits_per_search
        try:
            await supabase.update_api_key_credits(api_key.id, new_credits)
        except Exception as credit_error:
            logger.warning(f"Failed to update credits: {credit_error}")
            # Don't fail the request if credit update fails

        return SearchResponse(
            query=q,
            total_results=len(search_results),
            results=search_results,
            credits_used=settings.credits_per_search,
            credits_remaining=new_credits,
        )

    except Exception as e:
        # If DB fails during search, return error
        logger.error(f"Search error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse(
                error="Search failed",
                detail=str(e),
                code="SEARCH_ERROR",
            ).model_dump(),
        )


# ==================== Inventory Endpoint ====================

@router.get(
    "/supplier/{supplier_id}/inventory",
    response_model=InventoryResponse,
    tags=["Data"],
    summary="Get supplier inventory",
)
async def get_inventory(
    supplier_id: UUID,
    api_key: APIKey = Depends(validate_api_key),
) -> InventoryResponse:
    """
    Get all products for a specific supplier.

    Requires authentication and deducts 1 credit.
    """
    try:
        # Get supplier
        supplier = await supabase.get_supplier_by_id(str(supplier_id))

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Supplier not found",
                    detail=f"No supplier with ID {supplier_id}",
                    code="NOT_FOUND",
                ).model_dump(),
            )

        # Get products
        products = await supabase.get_products_by_supplier(str(supplier_id))

        # Deduct credits
        new_credits = api_key.credits_remaining - settings.credits_per_search
        await supabase.update_api_key_credits(api_key.id, new_credits)

        return InventoryResponse(
            supplier_id=supplier["id"],
            supplier_name=supplier["name"],
            products=[
                ProductResponse(
                    id=p["id"],
                    supplier_id=p["supplier_id"],
                    sku=p["sku_data"],
                    price_range=p["price_range"],
                    created_at=p["created_at"],
                    updated_at=p["updated_at"],
                )
                for p in products
            ],
            total_products=len(products),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse(
                error="Database unavailable",
                detail=str(e),
                code="DB_UNAVAILABLE",
            ).model_dump(),
        )


# ==================== Supplier Detail Endpoint ====================

@router.get(
    "/supplier/{supplier_id}",
    response_model=SupplierResponse,
    tags=["Data"],
    summary="Get supplier details",
)
async def get_supplier(
    supplier_id: UUID,
    api_key: APIKey = Depends(validate_api_key),
) -> SupplierResponse:
    """
    Get detailed information about a specific supplier.

    Requires authentication and deducts 1 credit.
    """
    try:
        supplier = await supabase.get_supplier_by_id(str(supplier_id))

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Supplier not found",
                    detail=f"No supplier with ID {supplier_id}",
                    code="NOT_FOUND",
                ).model_dump(),
            )

        # Deduct credits
        new_credits = api_key.credits_remaining - settings.credits_per_search
        await supabase.update_api_key_credits(api_key.id, new_credits)

        return SupplierResponse(
            id=supplier["id"],
            name=supplier["name"],
            industry_vector=supplier.get("industry_vector"),
            contact=supplier.get("contact_json", {}),
            verification_score=supplier.get("verification_score", 0.0),
            last_verified_at=supplier.get("last_verified_at"),
            created_at=supplier["created_at"],
            updated_at=supplier["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorResponse(
                error="Database unavailable",
                detail=str(e),
                code="DB_UNAVAILABLE",
            ).model_dump(),
        )


# Company Data Endpoints (Free Data Sources)
@router.get(
    "/companies/sample",
    response_model=SearchResponse,
    tags=["Data"],
    summary="Get sample company data",
)
async def get_sample_companies(
    q: Optional[str] = Query(None, description="Filter by sector or name"),
    api_key: APIKey = Depends(validate_api_key),
) -> SearchResponse:
    """
    Get sample company data - free demo data.
    Use this to test the API while we integrate real data sources.
    """
    companies = SAMPLE_COMPANIES
    
    if q:
        companies = [c for c in companies if q.lower() in (c.get("name", "") + c.get("sector", "")).lower()]
    
    results = [
        SearchResult(
            supplier=SupplierResponse(
                id=c.get("ticker", ""),
                name=c.get("name", ""),
                industry_vector=c.get("sector", ""),
                contact={},
                verification_score=1.0 if c.get("verified") else 0.0,
                last_verified_at=None,
                created_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-01T00:00:00Z",
            ),
            match_score=1.0,
            credits_used=0,
        )
        for c in companies
    ]
    
    return SearchResponse(
        query=q or "all companies",
        total_results=len(results),
        results=results,
        credits_used=0,
    )


@router.get(
    "/companies/{ticker}",
    response_model=SupplierResponse,
    tags=["Data"],
    summary="Get company by ticker",
)
async def get_company_by_ticker(
    ticker: str,
    api_key: APIKey = Depends(validate_api_key),
) -> SupplierResponse:
    """
    Get company info by stock ticker (e.g., AAPL, GOOGL).
    Uses free Yahoo Finance data.
    """
    if not DATA_SOURCES_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Data sources not available",
        )
    
    info = await get_company_info(ticker.upper())
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company {ticker} not found",
        )
    
    return SupplierResponse(
        id=ticker.upper(),
        name=info.get("name", ""),
        industry_vector=info.get("sector", ""),
        contact=info,
        verification_score=0.8,
        last_verified_at="2026-02-14T00:00:00Z",
        created_at="2026-02-14T00:00:00Z",
        updated_at="2026-02-14T00:00:00Z",
    )
