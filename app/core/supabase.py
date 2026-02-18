"""
Supabase HTTP Client for database operations.
Uses REST API instead of direct Postgres connection.
"""

import httpx
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from app.core.config import settings


class SupabaseClient:
    """Simple HTTP client for Supabase REST API."""

    def __init__(self):
        self.url = settings.supabase_url.rstrip("/")
        self.key = settings.supabase_key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        self._client: Optional[httpx.AsyncClient] = None

    @asynccontextmanager
    async def get_client(self):
        """Get async HTTP client."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            yield client

    async def query(
        self,
        table: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Any:
        """Execute a query against Supabase."""
        async with self.get_client() as client:
            if method.upper() == "GET":
                r = await client.get(
                    f"{self.url}/rest/v1/{table}",
                    headers=self.headers,
                    params=params,
                )
            elif method.upper() == "POST":
                r = await client.post(
                    f"{self.url}/rest/v1/{table}",
                    headers=self.headers,
                    json=data,
                )
            elif method.upper() == "PATCH":
                r = await client.patch(
                    f"{self.url}/rest/v1/{table}",
                    headers=self.headers,
                    json=data,
                )
            elif method.upper() == "DELETE":
                r = await client.delete(
                    f"{self.url}/rest/v1/{table}",
                    headers=self.headers,
                    params=params,
                )
            else:
                raise ValueError(f"Unknown method: {method}")

            r.raise_for_status()
            return r.json()

    # Table-specific methods
    async def get_suppliers(self, name_filter: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get suppliers with optional name filter."""
        params = {"select": "*", "limit": limit}
        
        if name_filter:
            # Build URL with filter directly to avoid URL encoding issues
            filter_url = f"{self.url}/rest/v1/suppliers?select=*&name=ilike.%{name_filter}%&limit={limit}"
            async with self.get_client() as client:
                r = await client.get(filter_url, headers=self.headers)
                r.raise_for_status()
                return r.json()
        
        return await self.query("suppliers", params=params)

    async def get_supplier_by_id(self, supplier_id: str) -> Optional[Dict]:
        """Get a single supplier by ID."""
        params = {"select": "*", "id": f"eq.{supplier_id}"}
        result = await self.query("suppliers", params=params)
        return result[0] if result else None

    async def get_products_by_supplier(self, supplier_id: str) -> List[Dict]:
        """Get all products for a supplier."""
        params = {"select": "*", "supplier_id": f"eq.{supplier_id}"}
        return await self.query("products", params=params)

    async def get_api_key(self, key_hash: str) -> Optional[Dict]:
        """Get API key by hash."""
        params = {"select": "*", "key_hash": f"eq.{key_hash}", "is_active": "eq.1"}
        result = await self.query("api_keys", params=params)
        return result[0] if result else None

    async def update_api_key_credits(self, key_id: str, credits: int) -> None:
        """Update API key credits."""
        await self.query(
            "api_keys",
            method="PATCH",
            params={"id": f"eq.{key_id}"},
            data={"credits_remaining": credits, "last_used_at": "now()"},
        )


# Global client instance
supabase = SupabaseClient()


async def check_health() -> tuple[bool, str]:
    """Check database health via Supabase API."""
    try:
        async with supabase.get_client() as client:
            r = await client.get(
                f"{supabase.url}/rest/v1/",
                headers=supabase.headers,
                timeout=5.0,
            )
            if r.status_code in (200, 400):  # 400 means API works but no table access
                return True, "healthy"
            return False, f"status: {r.status_code}"
    except Exception as e:
        return False, str(e)
