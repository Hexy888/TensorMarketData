#!/usr/bin/env python3
"""
CSV Ingestion Script for TensorMarketData.
Usage: python scripts/ingest_csv.py --file path/to/data.csv
"""

import argparse
import asyncio
import csv
import hashlib
import sys
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.models.domain import Supplier, Product
from app.models.schemas import ContactData, PriceRange, SKUData


async def generate_key(prefix: str = "tmd") -> tuple[str, str, str]:
    """Generate a new API key."""
    import secrets
    raw_key = f"{prefix}_sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]  # First 12 chars for display
    return raw_key, key_hash, key_prefix


async def ingest_suppliers(
    engine,
    file_path: str,
) -> dict[str, uuid4]:
    """
    Ingest suppliers from CSV file.
    Returns mapping of supplier names to IDs.
    """
    print(f"📂 Loading suppliers from: {file_path}")

    df = pd.read_csv(file_path)
    supplier_map = {}

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for _, row in df.iterrows():
            name = row.get("name", "").strip()
            if not name:
                continue

            # Check if supplier exists
            result = await session.execute(
                text("SELECT id FROM suppliers WHERE LOWER(name) = LOWER(:name)"),
                {"name": name},
            )
            existing = result.scalar_one_or_none()

            if existing:
                supplier_map[name] = existing
                print(f"  ↳ Found: {name}")
                continue

            # Create new supplier
            contact = {
                "email": row.get("email"),
                "phone": row.get("phone"),
                "linkedin": row.get("linkedin"),
            }

            supplier = Supplier(
                id=uuid4(),
                name=name,
                contact_json=contact,
                verification_score=float(row.get("verification_score", 0.0)),
            )
            session.add(supplier)
            await session.flush()
            supplier_map[name] = supplier.id
            print(f"  ➕ Created: {name}")

        await session.commit()

    print(f"\n✅ Processed {len(supplier_map)} suppliers")
    return supplier_map


async def ingest_products(
    engine,
    file_path: str,
    supplier_map: dict[str, uuid4],
) -> int:
    """
    Ingest products from CSV file.
    """
    print(f"\n📂 Loading products from: {file_path}")

    df = pd.read_csv(file_path)
    count = 0

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for _, row in df.iterrows():
            supplier_name = row.get("supplier_name")
            if not supplier_name or supplier_name not in supplier_map:
                print(f"  ⚠️  Skipping: unknown supplier '{supplier_name}'")
                continue

            supplier_id = supplier_map[supplier_name]

            # Check if product exists
            sku = row.get("sku", "").strip()
            result = await session.execute(
                text("SELECT id FROM products WHERE supplier_id = :supplier_id AND sku_data->>'sku' = :sku"),
                {"supplier_id": str(supplier_id), "sku": sku},
            )
            if result.scalar_one_or_found():
                print(f"  ↳ Found: {sku}")
                continue

            price_range = {
                "min": float(row.get("price_min", 0)),
                "max": float(row.get("price_max", 0)),
                "currency": row.get("currency", "USD"),
            }

            sku_data = {
                "sku": sku,
                "name": row.get("product_name"),
                "category": row.get("category"),
            }

            product = Product(
                id=uuid4(),
                supplier_id=supplier_id,
                sku_data=sku_data,
                price_range=price_range,
            )
            session.add(product)
            count += 1
            print(f"  ➕ Created: {sku}")

        await session.commit()

    print(f"\n✅ Created {count} products")
    return count


async def create_demo_api_key(engine) -> str:
    """Create a demo API key for testing."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        raw_key, key_hash, key_prefix = await generate_key("demo")

        await session.execute(
            text("""
                INSERT INTO api_keys (id, key_hash, key_prefix, credits_remaining, is_active)
                VALUES (:id, :hash, :prefix, :credits, 1)
            """),
            {
                "id": str(uuid4()),
                "hash": key_hash,
                "prefix": key_prefix,
                "credits": 100,
            },
        )
        await session.commit()

    return raw_key


async def main():
    parser = argparse.ArgumentParser(description="Ingest CSV data into TensorMarketData")
    parser.add_argument("--suppliers", type=str, help="Path to suppliers CSV file")
    parser.add_argument("--products", type=str, help="Path to products CSV file")
    parser.add_argument("--demo-key", action="store_true", help="Create demo API key")
    parser.add_argument(
        "--database-url",
        type=str,
        default=settings.database_url,
        help="Database connection URL",
    )

    args = parser.parse_args()

    if not any([args.suppliers, args.products, args.demo_key]):
        parser.print_help()
        print("\n❌ Error: Must specify --suppliers, --products, or --demo-key")
        return 1

    # Connect to database
    print("🔌 Connecting to database...")
    engine = create_async_engine(args.database_url, echo=False)

    try:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(__import__("app.core.database", fromlist=["Base"]).Base.metadata.create_all)

        supplier_map = {}

        # Ingest suppliers
        if args.suppliers:
            supplier_map = await ingest_suppliers(engine, args.suppliers)

        # Ingest products
        if args.products:
            await ingest_products(engine, args.products, supplier_map)

        # Create demo key
        if args.demo_key:
            key = await create_demo_api_key(engine)
            print(f"\n🔑 Demo API Key: {key}")
            print("   Store this key - it won't be shown again!")

        print("\n🎉 Ingestion complete!")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    finally:
        await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
