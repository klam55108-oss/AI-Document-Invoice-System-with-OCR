#!/usr/bin/env python3
"""Comprehensive script to reset/cleanup all data: pgvector, extracted_data, and persistent storage."""

import asyncio
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Load environment variables
load_dotenv()


async def check_database_state(session: AsyncSession):
    """Check current state of database tables."""
    print("\n📊 Checking database state...")
    
    # Check invoice_embeddings table
    try:
        check_embeddings = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'invoice_embeddings'
            )
        """)
        result = await session.execute(check_embeddings)
        embeddings_table_exists = result.scalar()
        
        if embeddings_table_exists:
            count_query = text("SELECT COUNT(*) FROM invoice_embeddings")
            result = await session.execute(count_query)
            embeddings_count = result.scalar() or 0
            print(f"   - invoice_embeddings: {embeddings_count} records")
        else:
            print(f"   - invoice_embeddings: table does not exist")
    except Exception as e:
        print(f"   - invoice_embeddings: error checking ({str(e)})")
    
    # Count other tables
    tables = [
        "invoices",
        "extracted_data",
        "validation_results",
        "processing_jobs",
    ]
    
    for table in tables:
        try:
            count_query = select(func.count()).select_from(text(table))
            result = await session.execute(count_query)
            count = result.scalar() or 0
            print(f"   - {table}: {count} records")
        except Exception as e:
            print(f"   - {table}: error checking ({str(e)})")


async def cleanup_pgvector(session: AsyncSession, dry_run: bool = False):
    """Clean up pgvector embeddings table."""
    print("\n🔍 Checking for pgvector data...")
    
    # Check if invoice_embeddings table exists
    check_table = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'invoice_embeddings'
        )
    """)
    result = await session.execute(check_table)
    table_exists = result.scalar()
    
    if not table_exists:
        print("   ✅ invoice_embeddings table does not exist - nothing to clean")
        return
    
    # Count records
    count_query = text("SELECT COUNT(*) FROM invoice_embeddings")
    result = await session.execute(count_query)
    count = result.scalar() or 0
    
    if count == 0:
        print("   ✅ invoice_embeddings table is empty - nothing to clean")
        return
    
    print(f"   📊 Found {count} embeddings in invoice_embeddings table")
    
    if dry_run:
        print("   🔍 DRY RUN: Would delete all embeddings")
        return
    
    # Delete all embeddings
    delete_query = text("DELETE FROM invoice_embeddings")
    await session.execute(delete_query)
    print(f"   ✅ Deleted {count} embeddings from invoice_embeddings")


async def cleanup_extracted_data(session: AsyncSession, dry_run: bool = False):
    """Clean up extracted_data and related tables."""
    print("\n🔍 Checking extracted_data and related tables...")
    
    # Count records
    tables = {
        "validation_results": "validation_results",
        "extracted_data": "extracted_data",
        "processing_jobs": "processing_jobs",
        "invoices": "invoices",
    }
    
    counts = {}
    for name, table in tables.items():
        try:
            count_query = select(func.count()).select_from(text(table))
            result = await session.execute(count_query)
            counts[name] = result.scalar() or 0
        except Exception as e:
            print(f"   ⚠️  Error counting {name}: {str(e)}")
            counts[name] = 0
    
    total = sum(counts.values())
    if total == 0:
        print("   ✅ All tables are empty - nothing to clean")
        return
    
    print(f"   📊 Found:")
    for name, count in counts.items():
        if count > 0:
            print(f"      - {name}: {count} records")
    
    if dry_run:
        print("   🔍 DRY RUN: Would delete all data from these tables")
        return
    
    # Delete in correct order (respecting foreign key constraints)
    print("\n   🧹 Deleting data...")
    
    # 1. Delete validation_results (references invoices)
    if counts["validation_results"] > 0:
        delete_query = text("DELETE FROM validation_results")
        await session.execute(delete_query)
        print(f"      ✅ Deleted {counts['validation_results']} validation_results")
    
    # 2. Delete extracted_data (references invoices)
    if counts["extracted_data"] > 0:
        delete_query = text("DELETE FROM extracted_data")
        await session.execute(delete_query)
        print(f"      ✅ Deleted {counts['extracted_data']} extracted_data")
    
    # 3. Delete processing_jobs (references invoices)
    if counts["processing_jobs"] > 0:
        delete_query = text("DELETE FROM processing_jobs")
        await session.execute(delete_query)
        print(f"      ✅ Deleted {counts['processing_jobs']} processing_jobs")
    
    # 4. Delete invoices (last, as other tables reference it)
    if counts["invoices"] > 0:
        delete_query = text("DELETE FROM invoices")
        await session.execute(delete_query)
        print(f"      ✅ Deleted {counts['invoices']} invoices")


async def cleanup_persistent_storage(data_dir: Path, dry_run: bool = False):
    """Clean up persistent storage (invoice files on disk)."""
    print("\n🔍 Checking persistent storage...")
    
    if not data_dir.exists():
        print(f"   ✅ Data directory does not exist: {data_dir}")
        return
    
    # Calculate total size and file count
    total_size = 0
    file_count = 0
    dirs_to_check = []
    
    for item in data_dir.iterdir():
        if item.is_file():
            total_size += item.stat().st_size
            file_count += 1
        elif item.is_dir():
            # Skip certain directories
            if item.name not in [".git", "__pycache__", "venv", ".venv"]:
                dirs_to_check.append(item)
                for file in item.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size
                        file_count += 1
    
    if file_count == 0:
        print(f"   ✅ No files found in {data_dir}")
        return
    
    size_mb = total_size / (1024 * 1024)
    print(f"   📊 Found {file_count} files ({size_mb:.2f} MB)")
    
    # Show directory structure
    if dirs_to_check:
        print(f"   📁 Directories:")
        for dir_path in sorted(dirs_to_check):
            dir_file_count = sum(1 for _ in dir_path.rglob("*") if _.is_file())
            print(f"      - {dir_path.name}/ ({dir_file_count} files)")
    
    if dry_run:
        print("   🔍 DRY RUN: Would delete all files and directories")
        return
    
    # Ask for confirmation
    print(f"\n   ⚠️  This will DELETE all files in {data_dir}")
    print(f"      - {file_count} files")
    print(f"      - {size_mb:.2f} MB")
    response = input("   Type 'DELETE FILES' to confirm: ").strip()
    
    if response != "DELETE FILES":
        print("   ❌ File deletion cancelled")
        return
    
    # Delete files and directories
    print("\n   🧹 Deleting files...")
    deleted_count = 0
    deleted_size = 0
    
    for item in data_dir.iterdir():
        if item.is_file():
            size = item.stat().st_size
            item.unlink()
            deleted_count += 1
            deleted_size += size
        elif item.is_dir() and item.name not in [".git", "__pycache__", "venv", ".venv"]:
            # Delete directory contents
            for file in item.rglob("*"):
                if file.is_file():
                    size = file.stat().st_size
                    file.unlink()
                    deleted_count += 1
                    deleted_size += size
            # Remove empty directories
            try:
                shutil.rmtree(item)
            except Exception as e:
                print(f"      ⚠️  Error removing {item}: {str(e)}")
    
    deleted_mb = deleted_size / (1024 * 1024)
    print(f"   ✅ Deleted {deleted_count} files ({deleted_mb:.2f} MB)")


async def reset_all_data(
    dry_run: bool = False,
    cleanup_vectors: bool = True,
    cleanup_extracted: bool = True,
    cleanup_files: bool = False,
):
    """Reset all data: pgvector, extracted_data, and optionally persistent storage.
    
    Args:
        dry_run: If True, only show what would be deleted
        cleanup_vectors: Clean up pgvector embeddings
        cleanup_extracted: Clean up extracted_data and related tables
        cleanup_files: Clean up persistent storage files (requires confirmation)
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in environment variables")
        sys.exit(1)
    
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    
    print("=" * 60)
    print("RESET ALL DATA - COMPREHENSIVE CLEANUP")
    print("=" * 60)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No data will be deleted")
    else:
        print("\n⚠️  WARNING: This will permanently delete data!")
        print("   - pgvector embeddings")
        print("   - extracted_data, validation_results, processing_jobs, invoices")
        if cleanup_files:
            print(f"   - All files in {data_dir}")
    
    print(f"\n🔗 Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with session_factory() as session:
            # Show current state
            await check_database_state(session)
            
            if not dry_run:
                # Ask for confirmation
                print("\n" + "=" * 60)
                print("⚠️  FINAL CONFIRMATION REQUIRED")
                print("=" * 60)
                print("This will permanently delete:")
                if cleanup_vectors:
                    print("  ✓ pgvector embeddings (invoice_embeddings)")
                if cleanup_extracted:
                    print("  ✓ extracted_data, validation_results, processing_jobs, invoices")
                if cleanup_files:
                    print(f"  ✓ All files in {data_dir}")
                print("\n🗑️  This action CANNOT be undone!")
                response = input("Type 'RESET ALL DATA' to confirm: ").strip()
                
                if response != "RESET ALL DATA":
                    print("❌ Reset cancelled. You must type exactly 'RESET ALL DATA' to confirm.")
                    return
            
            # Clean up pgvector
            if cleanup_vectors:
                await cleanup_pgvector(session, dry_run=dry_run)
            
            # Clean up extracted_data
            if cleanup_extracted:
                await cleanup_extracted_data(session, dry_run=dry_run)
            
            # Commit database changes
            if not dry_run and (cleanup_vectors or cleanup_extracted):
                await session.commit()
                print("\n✅ Database cleanup completed!")
            
            # Clean up persistent storage
            if cleanup_files:
                await cleanup_persistent_storage(data_dir, dry_run=dry_run)
            
            # Show final state
            if not dry_run:
                print("\n" + "=" * 60)
                print("📊 FINAL STATE")
                print("=" * 60)
                await check_database_state(session)
                print("\n✅ Reset completed!")
            
    except Exception as e:
        print(f"\n❌ Error during reset: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reset all data: pgvector, extracted_data, and persistent storage"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--no-vectors",
        action="store_true",
        help="Skip pgvector cleanup",
    )
    parser.add_argument(
        "--no-extracted",
        action="store_true",
        help="Skip extracted_data cleanup",
    )
    parser.add_argument(
        "--cleanup-files",
        action="store_true",
        help="Also delete persistent storage files (requires separate confirmation)",
    )
    
    args = parser.parse_args()
    
    asyncio.run(
        reset_all_data(
            dry_run=args.dry_run,
            cleanup_vectors=not args.no_vectors,
            cleanup_extracted=not args.no_extracted,
            cleanup_files=args.cleanup_files,
        )
    )

