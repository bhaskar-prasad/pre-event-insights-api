#!/usr/bin/env python3
"""Script to test Vault connection and database credentials."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import get_db_url


async def test_vault_connection():
    """Test if we can fetch credentials from Vault."""
    print("\n" + "=" * 60)
    print("VAULT CONNECTION TEST")
    print("=" * 60)

    print(f"\n📋 Configuration:")
    print(f"  VAULT_ENABLED: {settings.VAULT_ENABLED}")
    print(f"  VAULT_ADDR: {settings.VAULT_ADDR}")
    print(f"  VAULT_SECRET_PATH: {settings.VAULT_SECRET_PATH}")

    if not settings.VAULT_ENABLED:
        print("\n⚠️  Vault is DISABLED. Using environment variables.")
        print(f"  DB_HOST: {settings.DB_HOST}")
        print(f"  DB_PORT: {settings.DB_PORT}")
        print(f"  DB_USER: {settings.DB_USER}")
        print(f"  DB_NAME: {settings.DB_NAME}")
        return

    print("\n🔐 Attempting to fetch credentials from Vault...")

    try:
        db_url = await get_db_url()

        # Parse the URL to show credentials (without exposing the full URL)
        if "@" in db_url:
            user_pass, host_db = db_url.split("@")
            user_pass = user_pass.split("://")[1]  # Remove protocol
            user, _ = user_pass.split(":")
            host, db = host_db.split("/")
            port = host.split(":")[-1] if ":" in host else "5432"
            host = host.split(":")[0]

            print(f"\n✅ SUCCESS! Credentials fetched from Vault:")
            print(f"  Host: {host}")
            print(f"  Port: {port}")
            print(f"  User: {user}")
            print(f"  Database: {db}")
            print(f"  Connection String: postgresql+asyncpg://{user}:***@{host}:{port}/{db}")
        else:
            print(f"\n✅ SUCCESS! Got connection string: {db_url[:50]}...")

    except Exception as e:
        print(f"\n❌ ERROR: Failed to fetch credentials from Vault")
        print(f"  Error: {str(e)}")
        print(f"\n📚 Troubleshooting:")
        print(f"  1. Is Vault running? Run: vault server -dev")
        print(f"  2. Is VAULT_ADDR correct? Current: {settings.VAULT_ADDR}")
        print(f"  3. Is VAULT_TOKEN valid?")
        print(f"  4. Does the secret exist at path '{settings.VAULT_SECRET_PATH}'?")
        print(f"     Create it with: vault kv put {settings.VAULT_SECRET_PATH} \\")
        print(f"       username=postgres password=password host=localhost port=5432 database=fastapi_db")
        sys.exit(1)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_vault_connection())
    print("\n✨ Vault configuration is working correctly!\n")
