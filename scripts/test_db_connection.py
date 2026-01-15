#!/usr/bin/env python3
"""Test database connection and schema health."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.database import check_schema_health, init_db

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

async def main():
    """Test database connection."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not set in environment")
        print("💡 Tip: Create a .env file with DATABASE_URL=postgresql+asyncpg://...")
        return
    
    print(f"🔌 Testing database connection...")
    print(f"   Database URL: {database_url.split('@')[-1] if '@' in database_url else 'configured'}")
    
    try:
        # Initialize database
        await init_db(database_url)
        print("✅ Database connection successful")
        
        # Check schema health
        print("\n🔍 Checking schema health...")
        health = await check_schema_health()
        
        print(f"   Status: {health['status']}")
        if health.get('schema_version'):
            print(f"   Schema version: {health['schema_version']}")
        print(f"   Tables checked: {len(health.get('tables_checked', []))}")
        
        if health.get('missing_tables'):
            print(f"   ⚠️  Missing tables: {', '.join(health['missing_tables'])}")
        
        if health.get('errors'):
            print(f"   ⚠️  Errors found:")
            for error in health['errors']:
                print(f"      - {error}")
        
        if health['status'] == 'healthy':
            print("\n✅ Database schema is healthy")
        else:
            print("\n⚠️  Database schema has issues - run 'alembic upgrade head' to fix")
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("💡 Tip: Check your DATABASE_URL and ensure PostgreSQL is running")

if __name__ == "__main__":
    asyncio.run(main())

