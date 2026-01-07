#!/usr/bin/env python3
"""Inspect invoice status, errors, and extracted data."""

import asyncio
import os
import sys
import uuid
import json
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add project root to path
sys.path.append(os.getcwd())

from core.models import Invoice, ExtractedData, ProcessingStatus, ValidationResult

load_dotenv()

async def inspect_invoice(invoice_id_query: str):
    """Inspect invoice by ID or latest."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with session_factory() as session:
            # Determine invoice ID
            if invoice_id_query.lower() == "latest":
                stmt = select(Invoice).order_by(Invoice.created_at.desc()).limit(1)
                result = await session.execute(stmt)
                invoice = result.scalar_one_or_none()
            else:
                try:
                    invoice_id = uuid.UUID(invoice_id_query)
                    stmt = select(Invoice).where(Invoice.id == invoice_id)
                    result = await session.execute(stmt)
                    invoice = result.scalar_one_or_none()
                except ValueError:
                    # Try searching by filename
                    stmt = select(Invoice).where(Invoice.file_name.ilike(f"%{invoice_id_query}%")).limit(1)
                    result = await session.execute(stmt)
                    invoice = result.scalar_one_or_none()

            if not invoice:
                print(f"❌ Invoice not found: {invoice_id_query}")
                return

            print(f"\n{'='*20} INVOICE DETAILS {'='*20}")
            print(f"ID:       {invoice.id}")
            print(f"File:     {invoice.file_name}")
            print(f"Path:     {invoice.storage_path}")
            print(f"Type:     {invoice.file_type}")
            print(f"Status:   {invoice.processing_status.value}")
            print(f"Created:  {invoice.created_at}")
            
            if invoice.processing_status == ProcessingStatus.FAILED:
                print(f"\n❌ ERROR DETAILS:")
                print(f"Message:  {invoice.error_message or 'No error message recorded'}")

            # Fetch Extracted Data
            stmt = select(ExtractedData).where(ExtractedData.invoice_id == invoice.id)
            result = await session.execute(stmt)
            data = result.scalar_one_or_none()

            if data:
                print(f"\n{'='*20} EXTRACTED DATA {'='*20}")
                print(f"Vendor:   {data.vendor_name}")
                print(f"Inv #:    {data.invoice_number}")
                print(f"Date:     {data.invoice_date}")
                print(f"Total:    {data.total_amount} {data.currency or ''}")
                print(f"Subtotal: {data.subtotal}")
                print(f"Tax:      {data.tax_amount} (Rate: {data.tax_rate})")
                print(f"Confid:   {data.extraction_confidence:.2%}")
                
                print(f"\nLine Items ({len(data.line_items) if data.line_items else 0}):")
                if data.line_items:
                    for i, item in enumerate(data.line_items, 1):
                        amount = item.get('amount', 0)
                        desc = item.get('description', 'N/A')
                        print(f"  {i}. {desc[:50]:<50} | {amount:>10}")
                
                print(f"\nRAW TEXT PREVIEW (first 500 chars):")
                print("-" * 40)
                print(data.raw_text[:500] if data.raw_text else "No raw text")
                print("-" * 40)

            # Fetch Validation Results
            stmt = select(ValidationResult).where(ValidationResult.invoice_id == invoice.id)
            result = await session.execute(stmt)
            validations = result.scalars().all()

            if validations:
                print(f"\n{'='*20} VALIDATION RESULTS {'='*20}")
                for val in validations:
                    status_icon = "✅" if val.status.value == "passed" else "❌"
                    print(f"{status_icon} {val.rule_name:<30} | {val.status.value}")
                    if val.status.value == "failed":
                        print(f"   Error: {val.error_message}")

    except Exception as e:
        print(f"❌ Error inspecting invoice: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "latest"
    asyncio.run(inspect_invoice(query))
