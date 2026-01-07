#!/usr/bin/env python3
"""Check invoice processing status and error details."""

import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.models import Invoice, ProcessingStatus

load_dotenv()

async def check_invoice(invoice_id_str: str):
    """Check invoice status and error details."""
    import os
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set")
        return
    
    try:
        invoice_id = uuid.UUID(invoice_id_str)
    except ValueError:
        print(f"❌ Invalid invoice ID format: {invoice_id_str}")
        return
    
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with session_factory() as session:
            query = select(Invoice).where(Invoice.id == invoice_id)
            result = await session.execute(query)
            invoice = result.scalar_one_or_none()
            
            if not invoice:
                print(f"❌ Invoice not found: {invoice_id}")
                return
            
            print(f"📄 Invoice Details:")
            print(f"   ID: {invoice.id}")
            print(f"   File: {invoice.file_name}")
            print(f"   Path: {invoice.storage_path}")
            status_value = invoice.processing_status.value if hasattr(invoice.processing_status, 'value') else str(invoice.processing_status)
            print(f"   Status: {status_value}")
            print(f"   Created: {invoice.created_at}")
            
            if invoice.processing_status == ProcessingStatus.FAILED:
                print(f"\n❌ Processing Failed:")
                if invoice.error_message:
                    print(f"   Error: {invoice.error_message}")
                else:
                    print(f"   No error message recorded")
            
            if invoice.processed_at:
                print(f"   Processed: {invoice.processed_at}")
            
            print(f"\n📊 Additional Info:")
            print(f"   File Type: {invoice.file_type}")
            print(f"   File Size: {invoice.file_size} bytes" if invoice.file_size else "   File Size: N/A")
            print(f"   File Hash: {invoice.file_hash[:16]}..." if invoice.file_hash else "   File Hash: N/A")
            
    except Exception as e:
        print(f"❌ Error checking invoice: {str(e)}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/check_invoice_status.py <invoice_id>")
        sys.exit(1)
    
    asyncio.run(check_invoice(sys.argv[1]))

