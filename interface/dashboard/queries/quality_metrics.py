"""Quality metrics database queries for dashboard analytics."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any
from decimal import Decimal

from core.models import Invoice, ExtractedData, ProcessingStatus
from core.logging import get_logger

logger = get_logger(__name__)


async def get_quality_summary(session: AsyncSession) -> Dict[str, Any]:
    """Get overall quality metrics summary.
    
    Args:
        session: Async database session
        
    Returns:
        Dictionary with quality summary metrics:
        - total_invoices: Total count of invoices
        - critical_fields_complete: Dict with counts of non-NULL critical fields
        - avg_confidence: Dict with average confidence scores per field
    """
    logger.info("Fetching quality summary metrics")
    
    # Total invoices (completed only)
    total_result = await session.execute(
        select(func.count(Invoice.id)).where(Invoice.processing_status == ProcessingStatus.COMPLETED)
    )
    total_invoices = total_result.scalar() or 0
    
    # Critical fields completeness
    completeness_result = await session.execute(
        select(
            func.count(ExtractedData.invoice_id).label("total"),
            func.count(ExtractedData.vendor_name).label("vendor_present"),
            func.count(ExtractedData.invoice_number).label("invoice_num_present"),
            func.count(ExtractedData.invoice_date).label("invoice_date_present"),
            func.count(ExtractedData.total_amount).label("total_amount_present"),
            func.count(ExtractedData.subtotal).label("subtotal_present"),
            func.count(ExtractedData.tax_amount).label("tax_amount_present"),
            func.count(ExtractedData.currency).label("currency_present"),
        )
    )
    completeness = completeness_result.one()
    
    # Average confidence scores
    confidence_result = await session.execute(
        select(
            func.avg(ExtractedData.vendor_name_confidence).label("avg_vendor_conf"),
            func.avg(ExtractedData.invoice_number_confidence).label("avg_invoice_num_conf"),
            func.avg(ExtractedData.total_amount_confidence).label("avg_total_conf"),
        )
    )
    confidences = confidence_result.one()
    
    summary = {
        "total_invoices": total_invoices,
        "critical_fields_complete": {
            "vendor_name": completeness.vendor_present or 0,
            "invoice_number": completeness.invoice_num_present or 0,
            "invoice_date": completeness.invoice_date_present or 0,
            "total_amount": completeness.total_amount_present or 0,
            "subtotal": completeness.subtotal_present or 0,
            "tax_amount": completeness.tax_amount_present or 0,
            "currency": completeness.currency_present or 0,
        },
        "avg_confidence": {
            "vendor_name": float(confidences.avg_vendor_conf or 0),
            "invoice_number": float(confidences.avg_invoice_num_conf or 0),
            "total_amount": float(confidences.avg_total_conf or 0),
        },
    }
    
    logger.info(
        "Quality summary fetched",
        total_invoices=total_invoices,
        vendor_complete=summary["critical_fields_complete"]["vendor_name"],
    )
    
    return summary


async def get_quality_by_format(session: AsyncSession) -> List[Dict[str, Any]]:
    """Get quality metrics grouped by file format.
    
    Args:
        session: Async database session
        
    Returns:
        List of dictionaries, one per file type, with:
        - file_type: File format (pdf, xlsx, etc.)
        - total: Total invoices of this type
        - vendor_extracted: Count with vendor_name extracted
        - avg_vendor_conf: Average vendor confidence
        - avg_invoice_num_conf: Average invoice number confidence
        - avg_total_conf: Average total amount confidence
    """
    logger.info("Fetching quality metrics by file format")
    
    result = await session.execute(
        select(
            Invoice.file_type,
            func.count(Invoice.id).label("total"),
            func.count(ExtractedData.vendor_name).label("vendor_extracted"),
            func.avg(ExtractedData.vendor_name_confidence).label("avg_vendor_conf"),
            func.avg(ExtractedData.invoice_number_confidence).label("avg_invoice_num_conf"),
            func.avg(ExtractedData.total_amount_confidence).label("avg_total_conf"),
        )
        .join(ExtractedData, Invoice.id == ExtractedData.invoice_id, isouter=True)
        .where(Invoice.processing_status == ProcessingStatus.COMPLETED)
        .group_by(Invoice.file_type)
        .order_by(func.count(Invoice.id).desc())
    )
    
    by_format = [
        {
            "file_type": row.file_type,
            "total": row.total,
            "vendor_extracted": row.vendor_extracted or 0,
            "avg_vendor_conf": float(row.avg_vendor_conf or 0),
            "avg_invoice_num_conf": float(row.avg_invoice_num_conf or 0),
            "avg_total_conf": float(row.avg_total_conf or 0),
        }
        for row in result
    ]
    
    logger.info("Quality by format fetched", format_count=len(by_format))
    
    return by_format


async def get_low_confidence_invoices(
    session: AsyncSession,
    confidence_threshold: float = 0.7
) -> List[Dict[str, Any]]:
    """Get invoices with low confidence scores (below threshold).
    
    Args:
        session: Async database session
        confidence_threshold: Minimum confidence threshold (0.0-1.0)
        
    Returns:
        List of invoices with at least one confidence score below threshold
    """
    logger.info("Fetching low confidence invoices", threshold=confidence_threshold)
    
    result = await session.execute(
        select(
            Invoice.id,
            Invoice.file_name,
            Invoice.file_type,
            ExtractedData.vendor_name,
            ExtractedData.vendor_name_confidence,
            ExtractedData.invoice_number,
            ExtractedData.invoice_number_confidence,
            ExtractedData.total_amount,
            ExtractedData.total_amount_confidence,
        )
        .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
        .where(
            (ExtractedData.vendor_name_confidence < Decimal(str(confidence_threshold))) |
            (ExtractedData.invoice_number_confidence < Decimal(str(confidence_threshold))) |
            (ExtractedData.total_amount_confidence < Decimal(str(confidence_threshold))) |
            (ExtractedData.vendor_name_confidence.is_(None)) |
            (ExtractedData.invoice_number_confidence.is_(None)) |
            (ExtractedData.total_amount_confidence.is_(None))
        )
    )
    
    low_conf_invoices = [
        {
            "invoice_id": str(row.id),
            "file_name": row.file_name,
            "file_type": row.file_type,
            "vendor_name": row.vendor_name,
            "vendor_confidence": float(row.vendor_name_confidence) if row.vendor_name_confidence else None,
            "invoice_number": row.invoice_number,
            "invoice_num_confidence": float(row.invoice_number_confidence) if row.invoice_number_confidence else None,
            "total_amount": float(row.total_amount) if row.total_amount else None,
            "total_confidence": float(row.total_amount_confidence) if row.total_amount_confidence else None,
        }
        for row in result
    ]
    
    logger.info("Low confidence invoices fetched", count=len(low_conf_invoices))
    
    return low_conf_invoices


async def get_vendor_suggestions(session: AsyncSession, limit: int = 100) -> List[str]:
    """Get list of distinct vendor names for autocomplete suggestions.
    
    Args:
        session: Async database session
        limit: Maximum number of suggestions to return
        
    Returns:
        List of vendor names, ordered by frequency
    """
    result = await session.execute(
        select(
            ExtractedData.vendor_name,
            func.count(ExtractedData.vendor_name).label("count")
        )
        .where(ExtractedData.vendor_name.isnot(None))
        .group_by(ExtractedData.vendor_name)
        .order_by(func.count(ExtractedData.vendor_name).desc())
        .limit(limit)
    )
    
    vendors = [row.vendor_name for row in result]
    logger.info("Vendor suggestions fetched", count=len(vendors))
    
    return vendors


async def get_invoice_number_suggestions(session: AsyncSession, limit: int = 100) -> List[str]:
    """Get list of distinct invoice numbers for autocomplete suggestions.
    
    Args:
        session: Async database session
        limit: Maximum number of suggestions to return
        
    Returns:
        List of invoice numbers, ordered by recency
    """
    result = await session.execute(
        select(ExtractedData.invoice_number)
        .where(ExtractedData.invoice_number.isnot(None))
        .distinct()
        .order_by(ExtractedData.extracted_at.desc())
        .limit(limit)
    )
    
    invoice_numbers = [row.invoice_number for row in result]
    logger.info("Invoice number suggestions fetched", count=len(invoice_numbers))
    
    return invoice_numbers

