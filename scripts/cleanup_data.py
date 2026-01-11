#!/usr/bin/env python3
"""Unified data cleanup tool for invoices, vectors, and persistent storage."""

import asyncio
import os
import shutil
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add project root to path
sys.path.append(os.getcwd())

load_dotenv()

async def check_state(session: AsyncSession):
    """Print current database state."""
    print("\n📊 Current Database State:")
    tables = ["invoices", "extracted_data", "validation_results", "processing_jobs"]
    for table in tables:
        try:
            res = await session.execute(select(func.count()).select_from(text(table)))
            print(f"   - {table:<20}: {res.scalar()} records")
        except Exception:
            print(f"   - {table:<20}: Table not found")

    # Vector tables check
    try:
        vec_query = text("""
            SELECT count(*) FROM pg_class c 
            JOIN pg_namespace n ON n.oid = c.relnamespace 
            WHERE n.nspname = 'public' AND (c.relname LIKE 'llama_%' OR c.relname LIKE 'data_%' OR c.relname = 'invoice_embeddings')
        """)
        res = await session.execute(vec_query)
        print(f"   - Vector-related tables: {res.scalar()}")
    except Exception:
        pass

async def cleanup_invoices(session: AsyncSession, dry_run: bool, filter_path: str = None):
    """Clean up invoice-related database records."""
    print("\n🧹 Cleaning up invoice records...")
    
    where_clause = ""
    if filter_path:
        print(f"   (Filtering by path: %{filter_path}%)")
        where_clause = f"WHERE invoice_id IN (SELECT id FROM invoices WHERE storage_path LIKE '%{filter_path}%')"
        inv_where = f"WHERE storage_path LIKE '%{filter_path}%'"
    else:
        inv_where = ""

    tables_to_clean = ["validation_results", "extracted_data", "processing_jobs"]
    for table in tables_to_clean:
        count_query = text(f"SELECT COUNT(*) FROM {table} {where_clause}")
        count = (await session.execute(count_query)).scalar()
        if count > 0:
            if not dry_run:
                await session.execute(text(f"DELETE FROM {table} {where_clause}"))
                print(f"   ✅ Deleted {count} records from {table}")
            else:
                print(f"   🔍 DRY RUN: Would delete {count} records from {table}")

    # Finally invoices
    count_query = text(f"SELECT COUNT(*) FROM invoices {inv_where}")
    count = (await session.execute(count_query)).scalar()
    if count > 0:
        if not dry_run:
            await session.execute(text(f"DELETE FROM invoices {inv_where}"))
            print(f"   ✅ Deleted {count} invoices")
        else:
            print(f"   🔍 DRY RUN: Would delete {count} invoices")

async def cleanup_vectors(session: AsyncSession, dry_run: bool):
    """Clean up vector-related tables."""
    print("\n🧹 Cleaning up vector tables...")
    query = text("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND (tablename LIKE 'llama_%' OR tablename LIKE 'data_%' OR tablename LIKE 'vector_store_%' OR tablename = 'invoice_embeddings')
    """)
    result = await session.execute(query)
    tables = [row[0] for row in result.fetchall()]
    
    if not tables:
        print("   ✅ No vector tables found.")
        return

    for table in tables:
        if not dry_run:
            await session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
            print(f"   ✅ Dropped table {table}")
        else:
            print(f"   🔍 DRY RUN: Would drop table {table}")

def cleanup_storage(dry_run: bool):
    """Clean up files in data/ directory."""
    data_dir = Path("data")
    print(f"\n📂 Cleaning up storage in {data_dir}...")
    if not data_dir.exists():
        return

    files = [f for f in data_dir.rglob("*") if f.is_file() and not any(p in str(f) for p in [".git", "__pycache__", "venv"])]
    if not files:
        print("   ✅ No files found to delete.")
        return

    print(f"   📊 Found {len(files)} files.")
    if dry_run:
        print(f"   🔍 DRY RUN: Would delete {len(files)} files.")
        return

    confirm = input(f"⚠️  Confirm deleting {len(files)} files in {data_dir}? (y/N): ")
    if confirm.lower() == 'y':
        for f in files:
            f.unlink()
        print(f"   ✅ Deleted {len(files)} files.")
    else:
        print("   ❌ Storage cleanup cancelled.")

async def main():
    parser = argparse.ArgumentParser(description="Unified cleanup tool")
    parser.add_argument("--dry-run", action="store_true", help="Don't delete anything")
    parser.add_argument("--invoices", action="store_true", help="Clean up invoice database records")
    parser.add_argument("--vectors", action="store_true", help="Clean up vector/LlamaIndex tables")
    parser.add_argument("--storage", action="store_true", help="Clean up physical data/ storage")
    parser.add_argument("--all", action="store_true", help="Clean up everything")
    parser.add_argument("--filter", type=str, help="Filter invoices by path pattern")
    
    args = parser.parse_args()
    
    if not any([args.invoices, args.vectors, args.storage, args.all]):
        parser.print_help()
        return

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        await check_state(session)
        
        if args.invoices or args.all:
            await cleanup_invoices(session, args.dry_run, args.filter)
        
        if args.vectors or args.all:
            await cleanup_vectors(session, args.dry_run)
            
        if not args.dry_run:
            await session.commit()
            
    if args.storage or args.all:
        cleanup_storage(args.dry_run)

    print("\n✨ Cleanup finished.")
    await engine.dispose()

if __name__ == "__main__":
    import argparse
    asyncio.run(main())
