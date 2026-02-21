"""Pipeline for multi-dataset ingestion and deduplication."""

import asyncio
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_session
from core.models import Invoice, ExtractedData, InvoiceLineItem, ProcessingStatus
from core.logging import get_logger
from ingestion.hf_datasets.voxel51_adapter import Voxel51Adapter
from ingestion.hf_datasets.mychen76_adapter import Mychen76Adapter
from ingestion.hf_datasets.gokulraja_adapter import GokulRajaAdapter
from brain.schemas import CanonicalInvoiceSchema

logger = get_logger(__name__)

class IngestionPipeline:
    """Orchestrates multi-dataset ingestion."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.adapters = [
            Voxel51Adapter(),
            Mychen76Adapter(),
            GokulRajaAdapter()
        ]

    async def run(self, limit_per_dataset: int = 10):
        """Run the full ingestion pipeline."""
        logger.info(f"Starting ingestion pipeline (limit={limit_per_dataset} per dataset)")
        
        # 1. Load and normalize from all adapters
        all_records: List[CanonicalInvoiceSchema] = []
        for adapter in self.adapters:
            logger.info(f"Loading from adapter: {adapter.__class__.__name__}")
            records = await adapter.load(limit=limit_per_dataset)
            all_records.extend(records)
        
        logger.info(f"Loaded {len(all_records)} raw records. Starting deduplication...")

        # 2. Cross-dataset Deduplication using image_hash
        unique_records = []
        seen_hashes = set()
        
        # Also check against existing hashes in DB
        result = await self.session.execute(select(Invoice.image_hash).where(Invoice.image_hash.isnot(None)))
        existing_hashes = set(row[0] for row in result.fetchall())
        seen_hashes.update(existing_hashes)

        for record in all_records:
            if record.image_hash and record.image_hash in seen_hashes:
                logger.debug(f"Skipping duplicate record: {record.source_id} (hash={record.image_hash})")
                continue
            
            seen_hashes.add(record.image_hash)
            unique_records.append(record)

        logger.info(f"Found {len(unique_records)} unique records for ingestion.")

        # 3. Bulk Insert
        ingested_count = 0
        for record in unique_records:
            try:
                # Create Invoice
                invoice_id = uuid.uuid4()
                
                # Calculate file size and hash for file_hash (sha256)
                with open(record.image_path, "rb") as f:
                    content = f.read()
                    file_hash = hashlib.sha256(content).hexdigest()
                    file_size = len(content)

                invoice = Invoice(
                    id=invoice_id,
                    storage_path=record.image_path,
                    file_name=record.file_name,
                    category="huggingface",
                    group=record.source_dataset,
                    file_hash=file_hash,
                    file_size=file_size,
                    file_type="jpg",
                    version=1,
                    processing_status=ProcessingStatus.COMPLETED,
                    processed_at=datetime.now(timezone.utc),
                    # Multi-dataset fields
                    source_dataset=record.source_dataset,
                    source_id=record.source_id,
                    annotation_confidence=float(record.annotation_confidence),
                    image_hash=record.image_hash,
                    is_training_data=record.is_training_data,
                    raw_ocr_text=record.raw_ocr_text
                )
                self.session.add(invoice)

                # Create ExtractedData (backward compatibility & standard lookup)
                extracted = ExtractedData(
                    id=uuid.uuid4(),
                    invoice_id=invoice_id,
                    vendor_name=record.vendor_name,
                    invoice_number=record.invoice_number,
                    invoice_date=record.invoice_date,
                    total_amount=record.total_amount,
                    tax_amount=record.tax_amount,
                    subtotal=record.subtotal,
                    currency=record.currency,
                    raw_text=record.raw_ocr_text,
                    extraction_confidence=record.annotation_confidence
                )
                self.session.add(extracted)

                # Create Structured Line Items
                for item in record.line_items:
                    li = InvoiceLineItem(
                        invoice_id=invoice_id,
                        description=item.description,
                        quantity=item.quantity,
                        unit_price=item.unit_price,
                        total=item.amount,
                        tax_rate=item.tax_rate,
                        line_order=item.line_order
                    )
                    self.session.add(li)

                ingested_count += 1
                if ingested_count % 10 == 0:
                    await self.session.commit()

            except Exception as e:
                logger.error(f"Failed to ingest record {record.source_id}: {e}")
                await self.session.rollback()
                continue

        await self.session.commit()
        logger.info(f"Successfully ingested {ingested_count} records.")
        return ingested_count

async def main():
    """CLI entry point for pipeline."""
    from core.config import settings
    from core.database import init_db
    
    await init_db(settings.DATABASE_URL)
    async for session in get_session():
        pipeline = IngestionPipeline(session)
        await pipeline.run(limit_per_dataset=5)
        break

if __name__ == "__main__":
    asyncio.run(main())
