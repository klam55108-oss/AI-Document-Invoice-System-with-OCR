"""Database query utilities for dashboard data retrieval."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from core.models import ExtractedData, Invoice, ProcessingStatus, ValidationResult

# Global engine and session factory (shared across requests)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Get or create session factory with proper connection pooling.
    
    This function ensures the engine is properly initialized and can be
    called multiple times safely.
    """
    global _engine, _session_factory
    
    # If engine exists, check if it's still valid
    if _engine is not None:
        try:
            # Check if engine pool is closed
            if hasattr(_engine.pool, 'is_closed') and _engine.pool.is_closed():
                # Pool is closed, need to recreate
                _engine = None
                _session_factory = None
        except Exception:
            # Engine is in invalid state, recreate it
            _engine = None
            _session_factory = None
    
    if _engine is None:
        _engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        _session_factory = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    
    return _session_factory


async def get_invoice_list(status: ProcessingStatus | None = None) -> list[Invoice]:
    """Get list of invoices with optional status filter.

    Args:
        status: Optional processing status filter

    Returns:
        List of Invoice objects
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    # Create engine for this event loop (asyncio.run creates new loop each time)
    # This ensures connections are tied to the current event loop
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    try:
        # Join with extracted_data to get summary information
        from sqlalchemy.orm import selectinload
        
        query = (
            select(Invoice)
            .options(selectinload(Invoice.extracted_data))
            .order_by(Invoice.created_at.desc())
        )

        if status:
            query = query.where(Invoice.processing_status == status)

        # Use async context manager to ensure proper session lifecycle
        async with session_factory() as session:
            try:
                result = await session.execute(query)
                invoices = list(result.scalars().all())
                await session.commit()
                return invoices
            except Exception:
                await session.rollback()
                raise
    finally:
        # Dispose engine when done (cleans up connections for this event loop)
        await engine.dispose()


async def get_invoice_detail(invoice_id: UUID) -> dict | None:
    """Get detailed invoice information.

    Args:
        invoice_id: Invoice UUID

    Returns:
        Dictionary with invoice details or None if not found
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

    # Create engine for this event loop (asyncio.run creates new loop each time)
    # This ensures connections are tied to the current event loop
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    try:
        # Use async context manager to ensure proper session lifecycle
        async with session_factory() as session:
            try:
                # Get invoice
                invoice_query = select(Invoice).where(Invoice.id == invoice_id)
                invoice_result = await session.execute(invoice_query)
                invoice = invoice_result.scalar_one_or_none()

                if not invoice:
                    await session.commit()
                    return None

                # Get extracted data
                extracted_query = select(ExtractedData).where(ExtractedData.invoice_id == invoice_id)
                extracted_result = await session.execute(extracted_query)
                extracted_data = extracted_result.scalar_one_or_none()

                # Get validation results
                validation_query = select(ValidationResult).where(ValidationResult.invoice_id == invoice_id)
                validation_result = await session.execute(validation_query)
                validation_results = validation_result.scalars().all()

                # Build response dictionary
                result = {
                    "id": str(invoice.id),
                    "file_name": invoice.file_name,
                    "file_path": invoice.file_path,
                    "file_type": invoice.file_type,
                    "file_hash": invoice.file_hash,
                    "file_size": invoice.file_size,
                    "version": invoice.version,
                    "processing_status": invoice.processing_status.value if hasattr(invoice.processing_status, 'value') else str(invoice.processing_status),
                    "created_at": invoice.created_at,
                    "updated_at": invoice.updated_at,
                    "processed_at": invoice.processed_at,
                    "error_message": invoice.error_message,
                }

                if extracted_data:
                    result["extracted_data"] = {
                        "vendor_name": extracted_data.vendor_name,
                        "invoice_number": extracted_data.invoice_number,
                        "invoice_date": extracted_data.invoice_date,
                        "due_date": extracted_data.due_date,
                        "subtotal": float(extracted_data.subtotal) if extracted_data.subtotal else None,
                        "tax_amount": float(extracted_data.tax_amount) if extracted_data.tax_amount else None,
                        "tax_rate": float(extracted_data.tax_rate) if extracted_data.tax_rate else None,
                        "total_amount": float(extracted_data.total_amount) if extracted_data.total_amount else None,
                        "currency": extracted_data.currency,
                        "line_items": extracted_data.line_items,
                        "extraction_confidence": float(extracted_data.extraction_confidence) if extracted_data.extraction_confidence else None,
                    }

                if validation_results:
                    result["validation_results"] = [
                        {
                            "rule_name": vr.rule_name,
                            "rule_description": vr.rule_description,
                            "status": vr.status.value if hasattr(vr.status, 'value') else str(vr.status),
                            "expected_value": float(vr.expected_value) if vr.expected_value else None,
                            "actual_value": float(vr.actual_value) if vr.actual_value else None,
                            "tolerance": float(vr.tolerance) if vr.tolerance else None,
                            "error_message": vr.error_message,
                            "validated_at": vr.validated_at,
                        }
                        for vr in validation_results
                    ]

                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    finally:
        # Dispose engine when done (cleans up connections for this event loop)
        await engine.dispose()

