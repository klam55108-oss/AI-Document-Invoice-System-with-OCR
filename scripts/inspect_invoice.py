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

async def list_failed_invoices(limit: int = 20):
    """List recent failed invoices."""
    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        stmt = select(Invoice).where(Invoice.processing_status == ProcessingStatus.FAILED).order_by(Invoice.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        invoices = result.scalars().all()
        
        if not invoices:
            print("✅ No failed invoices found.")
            return

        print(f"\n❌ Recent Failed Invoices ({len(invoices)}):")
        print("-" * 80)
        print(f"{'ID':<38} | {'Filename':<30} | {'Error'}")
        print("-" * 80)
        for inv in invoices:
            error = (inv.error_message or "Unknown error")[:50]
            print(f"{str(inv.id):<38} | {inv.file_name[:30]:<30} | {error}")
    
    await engine.dispose()

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
                    # Try searching by filename or storage path
                    stmt = select(Invoice).where(
                        (Invoice.file_name.ilike(f"%{invoice_id_query}%")) | 
                        (Invoice.storage_path.ilike(f"%{invoice_id_query}%"))
                    ).order_by(Invoice.created_at.desc()).limit(1)
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
            status_value = invoice.processing_status.value if hasattr(invoice.processing_status, "value") else invoice.processing_status
            print(f"Status:   {status_value}")
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
                print(f"Confid:   {data.extraction_confidence:.2%}")
                
                if data.line_items:
                    print(f"\nLine Items ({len(data.line_items)}):")
                    for i, item in enumerate(data.line_items[:10], 1): # Show first 10
                        amount = item.get('amount', 0)
                        desc = item.get('description', 'N/A')
                        print(f"  {i}. {desc[:50]:<50} | {amount:>10}")
                    if len(data.line_items) > 10:
                        print(f"  ... and {len(data.line_items) - 10} more items.")
            
            # Fetch Validation Results
            stmt = select(ValidationResult).where(ValidationResult.invoice_id == invoice.id)
            result = await session.execute(stmt)
            validations = result.scalars().all()

            if validations:
                print(f"\n{'='*20} VALIDATION RESULTS {'='*20}")
                for val in validations:
                    val_status = val.status.value if hasattr(val.status, "value") else val.status
                    status_icon = "✅" if val_status == "passed" else "❌"
                    print(f"{status_icon} {val.rule_name:<30} | {val_status}")
                    if val_status == "failed":
                        print(f"   Error: {val.error_message}")

    except Exception as e:
        print(f"❌ Error inspecting invoice: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Inspect invoice details or list failures")
    parser.add_argument("query", nargs="?", default="latest", help="Invoice ID, filename, or 'latest'")
    parser.add_argument("--failed", action="store_true", help="List recent failed invoices")
    parser.add_argument("--limit", type=int, default=20, help="Limit for --failed list")
    
    args = parser.parse_args()
    
    if args.failed:
        asyncio.run(list_failed_invoices(args.limit))
    else:
        asyncio.run(inspect_invoice(args.query))
