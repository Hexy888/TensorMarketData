#!/usr/bin/env python3
"""
Generate API Key Script for TensorMarketData.
Usage: python scripts/generate_key.py [--credits 100] [--expires-days 30]
"""

import argparse
import asyncio
import hashlib
import sys
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


async def generate_key(prefix: str = "tmd") -> tuple[str, str, str, datetime | None]:
    """
    Generate a new API key.

    Returns:
        tuple: (full_key, key_hash, key_prefix, expires_at)
    """
    import secrets
    raw_key = f"{prefix}_sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]  # First 12 chars for display

    return raw_key, key_hash, key_prefix, None


async def create_api_key(
    engine,
    credits: int = 100,
    expires_days: int | None = None,
) -> dict:
    """
    Create a new API key in the database.
    """
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    raw_key, key_hash, key_prefix, expires_at = await generate_key()

    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    async with async_session() as session:
        await session.execute(
            text("""
                INSERT INTO api_keys (id, key_hash, key_prefix, credits_remaining, is_active, expires_at)
                VALUES (:id, :hash, :prefix, :credits, 1, :expires)
            """),
            {
                "id": str(uuid4()),
                "hash": key_hash,
                "prefix": key_prefix,
                "credits": credits,
                "expires": expires_at,
            },
        )
        await session.commit()

    return {
        "key": raw_key,
        "key_prefix": key_prefix,
        "credits": credits,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }


async def revoke_api_key(engine, key_prefix: str) -> bool:
    """
    Revoke an API key by prefix.
    """
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            text("UPDATE api_keys SET is_active = 0 WHERE key_prefix = :prefix"),
            {"prefix": key_prefix},
        )
        await session.commit()

        return result.rowcount > 0


async def list_api_keys(engine, include_inactive: bool = False) -> list[dict]:
    """
    List all API keys.
    """
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if include_inactive:
            result = await session.execute(
                text("""
                    SELECT id, key_prefix, credits_remaining, is_active, created_at, last_used_at, expires_at
                    FROM api_keys ORDER BY created_at DESC
                """),
            )
        else:
            result = await session.execute(
                text("""
                    SELECT id, key_prefix, credits_remaining, is_active, created_at, last_used_at, expires_at
                    FROM api_keys WHERE is_active = 1 ORDER BY created_at DESC
                """),
            )

        rows = result.fetchall()
        return [
            {
                "id": str(row[0]),
                "key_prefix": row[1],
                "credits": row[2],
                "is_active": bool(row[3]),
                "created_at": row[4].isoformat() if row[4] else None,
                "last_used_at": row[5].isoformat() if row[5] else None,
                "expires_at": row[6].isoformat() if row[6] else None,
            }
            for row in rows
        ]


async def main():
    parser = argparse.ArgumentParser(description="Manage TensorMarketData API Keys")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("--credits", type=int, default=100, help="Initial credits")
    create_parser.add_argument("--expires-days", type=int, default=None, help="Days until expiration")

    # Revoke command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API key")
    revoke_parser.add_argument("prefix", help="Key prefix to revoke")

    # List command
    subparsers.add_parser("list", help="List all API keys")
    subparsers.add_parser("list-all", help="List all API keys including revoked")

    # Add database URL to all
    for p in [create_parser, revoke_parser]:
        p.add_argument(
            "--database-url",
            type=str,
            default=settings.database_url,
            help="Database connection URL",
        )

    args = parser.parse_args()

    # Connect to database
    engine = create_async_engine(args.database_url, echo=False)

    try:
        if args.command == "create":
            key_info = await create_api_key(
                engine,
                credits=args.credits,
                expires_days=args.expires_days,
            )
            print("\n🔑 NEW API KEY CREATED")
            print("=" * 50)
            print(f"Key:      {key_info['key']}")
            print(f"Prefix:   {key_info['key_prefix']}")
            print(f"Credits:  {key_info['credits']}")
            print(f"Expires:  {key_info['expires_at'] or 'Never'}")
            print("=" * 50)
            print("⚠️  Store this key securely - it won't be shown again!")

        elif args.command == "revoke":
            success = await revoke_api_key(engine, args.prefix)
            if success:
                print(f"✅ Key with prefix '{args.prefix}' has been revoked")
            else:
                print(f"❌ No active key found with prefix '{args.prefix}'")

        elif args.command in ("list", "list-all"):
            include_inactive = args.command == "list-all"
            keys = await list_api_keys(engine, include_inactive)

            print(f"\n{'Active ' if not include_inactive else ''}API Keys ({len(keys)})")
            print("-" * 80)
            for key in keys:
                status = "✓" if key["is_active"] else "✗"
                print(f"{status} {key['key_prefix']}... | {key['credits']} credits | {'expired' if key['expires_at'] and datetime.fromisoformat(key['expires_at']) < datetime.utcnow() else 'active'}")
            print("-" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
