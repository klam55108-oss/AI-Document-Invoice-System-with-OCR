#!/usr/bin/env python3
"""Script to clean up invoice data from the database."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Load environment variables
load_dotenv()


async def cleanup_invoice_data(dry_run: bool = False, file_path_filter: str | None = None):
    """Clean up invoice data from the database.
    
    Args:
        dry_run: If True, only show what would be deleted without actually deleting
        file_path_filter: Optional filter to only delete invoices matching this path pattern
                         (e.g., "invoice-" to delete all invoices, or "data/" to delete old location)
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in environment variables")
        sys.exit(1)

    print(f"🔗 Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print("\n📊 Checking invoice data...")
            
            # Count invoices
            count_query = select(func.count()).select_from(text("invoices"))
            if file_path_filter:
                count_query = select(func.count()).select_from(
                    text("invoices")
                ).where(text(f"storage_path LIKE '%{file_path_filter}%'"))
            
            result = await session.execute(count_query)
            invoice_count = result.scalar() or 0
            
            # Count related data
            extracted_count_query = select(func.count()).select_from(text("extracted_data"))
            result = await session.execute(extracted_count_query)
            extracted_count = result.scalar() or 0
            
            validation_count_query = select(func.count()).select_from(text("validation_results"))
            result = await session.execute(validation_count_query)
            validation_count = result.scalar() or 0
            
            jobs_count_query = select(func.count()).select_from(text("processing_jobs"))
            result = await session.execute(jobs_count_query)
            jobs_count = result.scalar() or 0
            
            print(f"\n📋 Current database state:")
            print(f"   - Invoices: {invoice_count}")
            print(f"   - Extracted Data: {extracted_count}")
            print(f"   - Validation Results: {validation_count}")
            print(f"   - Processing Jobs: {jobs_count}")
            
            if invoice_count == 0:
                print("\n✅ No invoice data to clean up.")
                return
            
            # Show sample invoices
            sample_query = text("""
                SELECT id, file_name, storage_path, processing_status, created_at
                FROM invoices
                ORDER BY created_at DESC
                LIMIT 5
            """)
            result = await session.execute(sample_query)
            samples = result.fetchall()
            
            if samples:
                print(f"\n📄 Sample invoices (showing up to 5 most recent):")
                for inv_id, file_name, storage_path, status, created_at in samples:
                    print(f"   - {file_name} ({storage_path}) - {status} - {created_at}")
            
            if dry_run:
                print("\n🔍 DRY RUN MODE - No data will be deleted")
                print("   Run without --dry-run to actually delete the data")
                return
            
            # Ask for confirmation
            print(f"\n⚠️  This will DELETE all invoice data from the database:")
            print(f"   - {invoice_count} invoice records")
            print(f"   - {extracted_count} extracted data records")
            print(f"   - {validation_count} validation result records")
            print(f"   - {jobs_count} processing job records")
            
            if file_path_filter:
                print(f"\n   Filter: Only invoices with storage_path containing '{file_path_filter}'")
            
            print("\n🗑️  This action CANNOT be undone!")
            response = input("Type 'DELETE ALL' to confirm: ").strip()
            
            if response != "DELETE ALL":
                print("❌ Cleanup cancelled. You must type exactly 'DELETE ALL' to confirm.")
                return
            
            # Delete in correct order (respecting foreign key constraints)
            print("\n🧹 Cleaning up invoice data...")
            
            # 1. Delete validation results (references invoices)
            print("   Deleting validation results...")
            delete_validation = text("DELETE FROM validation_results")
            if file_path_filter:
                delete_validation = text(f"""
                    DELETE FROM validation_results 
                    WHERE invoice_id IN (
                        SELECT id FROM invoices WHERE storage_path LIKE '%{file_path_filter}%'
                    )
                """)
            await session.execute(delete_validation)
            print(f"   ✅ Deleted validation results")
            
            # 2. Delete extracted data (references invoices)
            print("   Deleting extracted data...")
            delete_extracted = text("DELETE FROM extracted_data")
            if file_path_filter:
                delete_extracted = text(f"""
                    DELETE FROM extracted_data 
                    WHERE invoice_id IN (
                        SELECT id FROM invoices WHERE storage_path LIKE '%{file_path_filter}%'
                    )
                """)
            await session.execute(delete_extracted)
            print(f"   ✅ Deleted extracted data")
            
            # 3. Delete processing jobs (references invoices)
            print("   Deleting processing jobs...")
            delete_jobs = text("DELETE FROM processing_jobs")
            if file_path_filter:
                delete_jobs = text(f"""
                    DELETE FROM processing_jobs 
                    WHERE invoice_id IN (
                        SELECT id FROM invoices WHERE storage_path LIKE '%{file_path_filter}%'
                    )
                """)
            await session.execute(delete_jobs)
            print(f"   ✅ Deleted processing jobs")
            
            # 4. Delete invoices (last, as other tables reference it)
            print("   Deleting invoices...")
            if file_path_filter:
                delete_invoices = text(f"DELETE FROM invoices WHERE storage_path LIKE '%{file_path_filter}%'")
            else:
                delete_invoices = text("DELETE FROM invoices")
            await session.execute(delete_invoices)
            print(f"   ✅ Deleted invoices")
            
            await session.commit()
            print("\n✅ Invoice data cleanup completed!")
            
            # Verify deletion
            result = await session.execute(select(func.count()).select_from(text("invoices")))
            remaining = result.scalar() or 0
            print(f"\n📊 Remaining invoices: {remaining}")
            
    except Exception as e:
        print(f"\n❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean up invoice data from database")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--file-path-filter",
        type=str,
        help="Only delete invoices matching this file path pattern (e.g., 'invoice-' or 'data/')",
    )
    
    args = parser.parse_args()
    
    asyncio.run(cleanup_invoice_data(dry_run=args.dry_run, file_path_filter=args.file_path_filter))

