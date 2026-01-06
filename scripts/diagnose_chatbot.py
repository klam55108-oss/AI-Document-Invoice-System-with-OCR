"""Diagnostic script to check chatbot data availability."""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func, text

from core.models import Invoice, ExtractedData

load_dotenv()


async def diagnose_chatbot_data():
    """Check if data exists for chatbot queries."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as session:
            print("🔍 Diagnosing Chatbot Data Availability\n")

            # 1. Check total invoices
            stmt = select(func.count(Invoice.id))
            result = await session.execute(stmt)
            total_invoices = result.scalar()
            print(f"📊 Total invoices in database: {total_invoices}")

            if total_invoices == 0:
                print("⚠️  No invoices found in database!")
                print("   → This is a DATA issue. Process some invoices first.")
                return

            # 2. Check invoices with extracted data
            stmt = (
                select(func.count(Invoice.id))
                .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
            )
            result = await session.execute(stmt)
            invoices_with_data = result.scalar()
            print(f"📄 Invoices with extracted data: {invoices_with_data}")

            # 3. Check for jimeng dataset
            stmt = (
                select(func.count(Invoice.id))
                .where(
                    func.jsonb_extract_path_text(Invoice.upload_metadata, "subfolder").ilike("%jimeng%")
                )
            )
            result = await session.execute(stmt)
            jimeng_count = result.scalar()
            print(f"📁 Invoices from 'jimeng' folder: {jimeng_count}")

            # 4. Check upload_metadata structure
            stmt = select(Invoice.upload_metadata).where(Invoice.upload_metadata.isnot(None)).limit(5)
            result = await session.execute(stmt)
            metadata_samples = result.fetchall()
            if metadata_samples:
                print(f"\n📋 Sample upload_metadata (first {len(metadata_samples)}):")
                for i, (meta,) in enumerate(metadata_samples, 1):
                    print(f"   {i}. {meta}")
            else:
                print("\n⚠️  No invoices have upload_metadata set")
                print("   → This might be why 'jimeng' queries fail")

            # 5. Check invoice_embeddings table
            try:
                stmt = text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'invoice_embeddings'
                """)
                result = await session.execute(stmt)
                table_exists = result.scalar() > 0

                if table_exists:
                    stmt = text("SELECT COUNT(*) FROM invoice_embeddings")
                    result = await session.execute(stmt)
                    embedding_count = result.scalar()
                    print(f"\n🔢 invoice_embeddings table exists: ✅")
                    print(f"   Embeddings count: {embedding_count}")
                else:
                    print(f"\n🔢 invoice_embeddings table exists: ❌")
                    print("   → Vector search will fail, but database fallback should work")
            except Exception as e:
                print(f"\n⚠️  Error checking invoice_embeddings: {e}")

            # 6. Sample invoice data
            print(f"\n📝 Sample invoice data (first 3):")
            stmt = (
                select(Invoice, ExtractedData)
                .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                .limit(3)
            )
            result = await session.execute(stmt)
            rows = result.all()
            for i, (invoice, extracted) in enumerate(rows, 1):
                print(f"\n   Invoice {i}:")
                print(f"      ID: {invoice.id}")
                print(f"      File: {invoice.file_name}")
                print(f"      Vendor: {extracted.vendor_name}")
                print(f"      Invoice #: {extracted.invoice_number}")
                print(f"      Total: {extracted.total_amount} {extracted.currency}")
                if invoice.upload_metadata:
                    print(f"      Metadata: {invoice.upload_metadata}")

            # 7. Test search queries
            print(f"\n🔍 Testing search queries:")

            # Test vendor search
            stmt = (
                select(func.count(Invoice.id))
                .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                .where(ExtractedData.vendor_name.isnot(None))
            )
            result = await session.execute(stmt)
            vendors_count = result.scalar()
            print(f"   Invoices with vendor names: {vendors_count}")

            # Test file name search
            stmt = select(func.count(Invoice.id)).where(Invoice.file_name.ilike("%jimeng%"))
            result = await session.execute(stmt)
            jimeng_files = result.scalar()
            print(f"   Files with 'jimeng' in name: {jimeng_files}")

            # 8. Summary
            print(f"\n📊 DIAGNOSIS SUMMARY:")
            print(f"   Total invoices: {total_invoices}")
            print(f"   With extracted data: {invoices_with_data}")
            print(f"   From jimeng folder: {jimeng_count}")
            print(f"   Vector embeddings table: {'✅' if table_exists else '❌'}")

            if total_invoices == 0:
                print("\n❌ ISSUE: No invoices in database")
                print("   SOLUTION: Process some invoices first")
            elif invoices_with_data == 0:
                print("\n❌ ISSUE: No invoices have extracted data")
                print("   SOLUTION: Ensure invoices are processed and have extracted_data")
            elif jimeng_count == 0 and not metadata_samples:
                print("\n⚠️  WARNING: No jimeng invoices found via metadata")
                print("   → Queries about 'jimeng' might not work")
                print("   → But general invoice queries should work")
            else:
                print("\n✅ Data looks good! Issue might be in:")
                print("   1. LLM not being called (check DEEPSEEK_API_KEY)")
                print("   2. Search logic not matching queries")
                print("   3. Response generation failing")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(diagnose_chatbot_data())

