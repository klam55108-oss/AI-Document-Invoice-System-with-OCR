"""Update existing HuggingFace dataset records with individual field confidences.

This script fixes records where extraction_confidence is set but individual field
confidences (vendor_name_confidence, etc.) are missing or 0.
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session, init_db
from core.config import settings
from core.models import Invoice, ExtractedData
from core.logging import get_logger

logger = get_logger(__name__)


async def update_field_confidences():
    """Update field confidences for HuggingFace dataset records."""
    await init_db(settings.DATABASE_URL)
    
    async for session in get_session():
        # Find records from HuggingFace datasets with missing field confidences
        stmt = (
            select(ExtractedData, Invoice)
            .join(Invoice, ExtractedData.invoice_id == Invoice.id)
            .where(
                Invoice.category == "huggingface",
                ExtractedData.extraction_confidence > 0,
                # Field confidences are missing or 0
                (ExtractedData.vendor_name_confidence == None) | (ExtractedData.vendor_name_confidence == 0)
            )
        )
        
        result = await session.execute(stmt)
        records = result.fetchall()
        
        logger.info(f"Found {len(records)} HuggingFace records to update")
        
        if not records:
            logger.info("No records need updating")
            return
        
        # Update each record
        updated_count = 0
        for extracted_data, invoice in records:
            # Use extraction_confidence (or annotation_confidence) as default field confidence
            field_conf = extracted_data.extraction_confidence or invoice.annotation_confidence
            
            if field_conf and field_conf > 0:
                # Update individual field confidences
                extracted_data.vendor_name_confidence = field_conf if extracted_data.vendor_name else None
                extracted_data.invoice_number_confidence = field_conf if extracted_data.invoice_number else None
                extracted_data.invoice_date_confidence = field_conf if extracted_data.invoice_date else None
                extracted_data.total_amount_confidence = field_conf if extracted_data.total_amount else None
                extracted_data.tax_amount_confidence = field_conf if extracted_data.tax_amount else None
                extracted_data.subtotal_confidence = field_conf if extracted_data.subtotal else None
                extracted_data.currency_confidence = field_conf if extracted_data.currency else None
                
                updated_count += 1
                
                if updated_count % 50 == 0:
                    await session.commit()
                    logger.info(f"Updated {updated_count} records...")
        
        await session.commit()
        logger.info(f"Successfully updated {updated_count} records with field confidences")
        break


if __name__ == "__main__":
    asyncio.run(update_field_confidences())
