#!/usr/bin/env python3
"""Script to clean up all pgvector data from the database."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Load environment variables
load_dotenv()


async def cleanup_vector_data():
    """Clean up all pgvector-related data from the database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in environment variables")
        sys.exit(1)

    print(f"🔗 Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print("\n📊 Checking for vector-related tables...")
            
            # Query to find all tables that might contain vector data
            # LlamaIndex typically creates tables with names like:
            # - data_* (for document chunks)
            # - vector_store_* (for vector stores)
            # - Any table with vector columns
            
            # First, check for tables with vector columns
            vector_tables_query = text("""
                SELECT 
                    n.nspname as schemaname,
                    c.relname as tablename,
                    a.attname as column_name
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                JOIN pg_type t ON a.atttypid = t.oid
                WHERE t.typname = 'vector'
                AND n.nspname = 'public'
                AND a.attnum > 0
                AND NOT a.attisdropped
                ORDER BY c.relname, a.attname;
            """)
            
            result = await session.execute(vector_tables_query)
            vector_tables = result.fetchall()
            
            if not vector_tables:
                print("✅ No vector columns found in any tables.")
                print("   (LlamaIndex VectorStoreIndex may be using in-memory storage)")
            else:
                print(f"📋 Found {len(vector_tables)} table(s) with vector columns:")
                for schema, table, column in vector_tables:
                    print(f"   - {schema}.{table}.{column}")
            
            # Check for LlamaIndex-specific tables
            llama_tables_query = text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND (
                    tablename LIKE 'data_%' 
                    OR tablename LIKE 'vector_store_%'
                    OR tablename LIKE 'llama_%'
                )
                ORDER BY tablename;
            """)
            
            result = await session.execute(llama_tables_query)
            llama_tables = result.fetchall()
            
            if llama_tables:
                print(f"\n📋 Found {len(llama_tables)} LlamaIndex-related table(s):")
                for (table_name,) in llama_tables:
                    print(f"   - {table_name}")
            
            # Get all tables with vector data
            all_vector_tables = set()
            for schema, table, column in vector_tables:
                all_vector_tables.add(f"{schema}.{table}")
            for (table_name,) in llama_tables:
                all_vector_tables.add(f"public.{table_name}")
            
            if not all_vector_tables:
                print("\n✅ No vector data tables found. Database is clean.")
                await session.commit()
                return
            
            # Ask for confirmation
            print(f"\n⚠️  Found {len(all_vector_tables)} table(s) with vector data:")
            for table in sorted(all_vector_tables):
                print(f"   - {table}")
            
            print("\n🗑️  This will DELETE all vector data from these tables.")
            response = input("Continue? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("❌ Cleanup cancelled.")
                return
            
            # Clean up vector data
            print("\n🧹 Cleaning up vector data...")
            
            for table in sorted(all_vector_tables):
                try:
                    # Truncate table (faster than DELETE)
                    truncate_query = text(f'TRUNCATE TABLE {table} CASCADE;')
                    await session.execute(truncate_query)
                    print(f"   ✅ Truncated {table}")
                except Exception as e:
                    print(f"   ⚠️  Error truncating {table}: {str(e)}")
                    # Try dropping the table if truncate fails
                    try:
                        drop_query = text(f'DROP TABLE IF EXISTS {table} CASCADE;')
                        await session.execute(drop_query)
                        print(f"   ✅ Dropped {table}")
                    except Exception as e2:
                        print(f"   ❌ Error dropping {table}: {str(e2)}")
            
            await session.commit()
            print("\n✅ Vector data cleanup completed!")
            
            # Show remaining vector tables (should be empty now)
            result = await session.execute(vector_tables_query)
            remaining = result.fetchall()
            if remaining:
                print(f"\n📊 Remaining vector tables (now empty):")
                for schema, table, column in remaining:
                    print(f"   - {schema}.{table}.{column}")
            
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


async def list_vector_tables():
    """List all vector-related tables without cleaning them."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in environment variables")
        sys.exit(1)

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            # Check for tables with vector columns
            vector_tables_query = text("""
                SELECT 
                    n.nspname as schemaname,
                    c.relname as tablename,
                    a.attname as column_name
                FROM pg_attribute a
                JOIN pg_class c ON a.attrelid = c.oid
                JOIN pg_namespace n ON c.relnamespace = n.oid
                JOIN pg_type t ON a.atttypid = t.oid
                WHERE t.typname = 'vector'
                AND n.nspname = 'public'
                AND a.attnum > 0
                AND NOT a.attisdropped
                ORDER BY c.relname, a.attname;
            """)
            
            result = await session.execute(vector_tables_query)
            vector_tables = result.fetchall()
            
            # Check for LlamaIndex tables
            llama_tables_query = text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND (
                    tablename LIKE 'data_%' 
                    OR tablename LIKE 'vector_store_%'
                    OR tablename LIKE 'llama_%'
                )
                ORDER BY tablename;
            """)
            
            result2 = await session.execute(llama_tables_query)
            llama_tables = result2.fetchall()
            
            print("📊 Vector-related tables in database:")
            if vector_tables:
                print("\nTables with vector columns:")
                for schema, table, column in vector_tables:
                    print(f"   - {schema}.{table}.{column}")
            else:
                print("\n   No tables with vector columns found.")
            
            if llama_tables:
                print("\nLlamaIndex-related tables:")
                for (table_name,) in llama_tables:
                    print(f"   - {table_name}")
            else:
                print("\n   No LlamaIndex-related tables found.")
            
            await session.commit()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up pgvector data from database")
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list vector tables without cleaning them",
    )
    
    args = parser.parse_args()
    
    if args.list_only:
        asyncio.run(list_vector_tables())
    else:
        asyncio.run(cleanup_vector_data())

