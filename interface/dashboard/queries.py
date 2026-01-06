"""Database query utilities for dashboard data retrieval."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from core.models import ExtractedData, Invoice, ProcessingStatus, ValidationResult, ValidationStatus

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


async def get_invoice_list(
    status: ProcessingStatus | None = None,
    search_query: str | None = None,
    date_range: tuple | None = None,
    vendor: str | None = None,
    amount_min: float | None = None,
    amount_max: float | None = None,
    confidence_min: float | None = None,
    validation_status: str | None = None,
) -> list[Invoice]:
    """Get list of invoices with optional filters.

    Args:
        status: Optional processing status filter
        search_query: Optional search string (matches file name or vendor)
        date_range: Optional tuple of (start_date, end_date)
        vendor: Optional vendor name filter (partial match)
        amount_min: Optional minimum total amount filter
        amount_max: Optional maximum total amount filter
        confidence_min: Optional minimum extraction confidence filter (0.0-1.0)
        validation_status: Optional validation status filter ("all_passed", "has_failed", "has_warning")

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
            .outerjoin(Invoice.extracted_data)
            .options(
                selectinload(Invoice.extracted_data),
                selectinload(Invoice.validation_results)
            )
            .order_by(Invoice.created_at.desc())
        )

        if status:
            query = query.where(Invoice.processing_status == status)
            
        if search_query:
            from sqlalchemy import or_
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    Invoice.file_name.ilike(search_pattern),
                    ExtractedData.vendor_name.ilike(search_pattern)
                )
            )
            
        if date_range and len(date_range) == 2:
            start_date, end_date = date_range
            if start_date:
                query = query.where(Invoice.created_at >= start_date)
            if end_date:
                # Add one day to end_date to include all of that day
                from datetime import timedelta
                query = query.where(Invoice.created_at < end_date + timedelta(days=1))
        
        # Apply advanced filters
        if vendor:
            vendor_pattern = f"%{vendor}%"
            query = query.where(ExtractedData.vendor_name.ilike(vendor_pattern))
        
        if amount_min is not None:
            query = query.where(ExtractedData.total_amount >= amount_min)
        
        if amount_max is not None:
            query = query.where(ExtractedData.total_amount <= amount_max)
        
        if confidence_min is not None:
            query = query.where(ExtractedData.extraction_confidence >= confidence_min)
        
        if validation_status:
            from core.models import ValidationResult, ValidationStatus
            
            if validation_status == "all_passed":
                # All validations passed - exclude invoices with failures
                subquery = (
                    select(ValidationResult.invoice_id)
                    .where(ValidationResult.status == ValidationStatus.FAILED)
                    .distinct()
                )
                query = query.where(~Invoice.id.in_(subquery))
            elif validation_status == "has_failed":
                # Has at least one failed validation
                subquery = (
                    select(ValidationResult.invoice_id)
                    .where(ValidationResult.status == ValidationStatus.FAILED)
                    .distinct()
                )
                query = query.where(Invoice.id.in_(subquery))
            elif validation_status == "has_warning":
                # Has at least one warning
                subquery = (
                    select(ValidationResult.invoice_id)
                    .where(ValidationResult.status == ValidationStatus.WARNING)
                    .distinct()
                )
                query = query.where(Invoice.id.in_(subquery))

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
                    "storage_path": invoice.storage_path,
                    "category": invoice.category,
                    "group": invoice.group,
                    "job_id": str(invoice.job_id) if invoice.job_id else None,
                    "file_type": invoice.file_type,
                    "file_hash": invoice.file_hash,
                    "file_size": invoice.file_size,
                    "version": invoice.version,
                    "processing_status": invoice.processing_status.value if hasattr(invoice.processing_status, 'value') else str(invoice.processing_status),
                    "created_at": invoice.created_at,
                    "updated_at": invoice.updated_at,
                    "processed_at": invoice.processed_at,
                    "error_message": invoice.error_message,
                    "upload_metadata": invoice.upload_metadata,
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


async def get_status_distribution() -> dict[str, int]:
    """Get invoice processing status distribution for charts.

    Returns:
        Dictionary mapping status names to counts
        Example: {"completed": 150, "failed": 10, "processing": 5}
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

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
        async with session_factory() as session:
            try:
                query = select(
                    Invoice.processing_status,
                    func.count(Invoice.id).label("count"),
                ).group_by(Invoice.processing_status)

                result = await session.execute(query)
                rows = result.all()

                status_counts: dict[str, int] = {}
                for row in rows:
                    status = row.processing_status
                    status_str = status.value if hasattr(status, "value") else str(status)
                    status_counts[status_str] = row.count

                await session.commit()
                return status_counts
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()


async def get_time_series_data(
    aggregation: str = "daily",
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """Get time series data for processing volume trends.

    Args:
        aggregation: Time aggregation level ("daily", "weekly", "monthly")
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of dictionaries with "date" and "count" keys
        Example: [{"date": "2025-01-01", "count": 25}, ...]
    """
    import os
    from dotenv import load_dotenv
    from typing import Any

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

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
        async with session_factory() as session:
            try:
                # Determine date truncation based on aggregation
                if aggregation == "daily":
                    date_expr = func.date(Invoice.created_at)
                elif aggregation == "weekly":
                    date_expr = func.date_trunc("week", Invoice.created_at)
                elif aggregation == "monthly":
                    date_expr = func.date_trunc("month", Invoice.created_at)
                else:
                    date_expr = func.date(Invoice.created_at)

                query = select(
                    date_expr.label("date"),
                    func.count(Invoice.id).label("count"),
                ).group_by(date_expr)

                if start_date:
                    query = query.where(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))
                if end_date:
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    query = query.where(Invoice.created_at <= end_datetime)

                query = query.order_by(date_expr)

                result = await session.execute(query)
                rows = result.all()

                series_data = []
                for row in rows:
                    series_data.append(
                        {
                            "date": row.date.isoformat() if isinstance(row.date, date) else row.date.strftime("%Y-%m-%d"),
                            "count": row.count,
                        }
                    )

                await session.commit()
                return series_data
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()


async def get_vendor_analysis_data(
    sort_by: str = "count",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Get vendor analysis data for charts.

    Args:
        sort_by: Sort by "count" or "amount"
        limit: Number of top vendors to return

    Returns:
        List of dictionaries with vendor information
        Example: [{"vendor": "Vendor A", "invoice_count": 50, "total_amount": 100000.00}, ...]
    """
    import os
    from dotenv import load_dotenv
    from typing import Any

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

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
        async with session_factory() as session:
            try:
                query = (
                    select(
                        ExtractedData.vendor_name.label("vendor"),
                        func.count(func.distinct(Invoice.id)).label("invoice_count"),
                        func.coalesce(func.sum(ExtractedData.total_amount), 0).label("total_amount"),
                    )
                    .select_from(Invoice)
                    .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                    .where(ExtractedData.vendor_name.isnot(None))
                    .group_by(ExtractedData.vendor_name)
                )

                if sort_by == "count":
                    query = query.order_by(func.count(func.distinct(Invoice.id)).desc())
                else:
                    query = query.order_by(func.sum(ExtractedData.total_amount).desc())

                query = query.limit(limit)

                result = await session.execute(query)
                rows = result.all()

                vendor_data = []
                for row in rows:
                    vendor_data.append(
                        {
                            "vendor": row.vendor,
                            "invoice_count": row.invoice_count,
                            "total_amount": float(row.total_amount) if row.total_amount else 0.0,
                        }
                    )

                await session.commit()
                return vendor_data
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()


async def get_financial_summary_data() -> dict[str, Any]:
    """Get financial summary data for charts.

    Returns:
        Dictionary with financial aggregates
        Example: {
            "total_amount": 500000.00,
            "total_tax": 50000.00,
            "tax_breakdown": [{"rate": 0.10, "amount": 50000.00}, ...],
            "currency_distribution": [{"currency": "USD", "count": 100}, ...]
        }
    """
    import os
    from dotenv import load_dotenv
    from typing import Any

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not set")

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
        async with session_factory() as session:
            try:
                # Get totals for completed invoices only
                totals_query = (
                    select(
                        func.coalesce(func.sum(ExtractedData.total_amount), 0).label("total_amount"),
                        func.coalesce(func.sum(ExtractedData.tax_amount), 0).label("total_tax"),
                    )
                    .select_from(Invoice)
                    .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                    .where(Invoice.processing_status == ProcessingStatus.COMPLETED)
                )

                totals_result = await session.execute(totals_query)
                totals_row = totals_result.one()

                # Get tax breakdown
                tax_query = (
                    select(
                        ExtractedData.tax_rate,
                        func.sum(ExtractedData.tax_amount).label("amount"),
                    )
                    .select_from(Invoice)
                    .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                    .where(
                        Invoice.processing_status == ProcessingStatus.COMPLETED,
                        ExtractedData.tax_rate.isnot(None),
                        ExtractedData.tax_amount.isnot(None),
                    )
                    .group_by(ExtractedData.tax_rate)
                    .order_by(func.sum(ExtractedData.tax_amount).desc())
                )

                tax_result = await session.execute(tax_query)
                tax_rows = tax_result.all()

                tax_breakdown = []
                for row in tax_rows:
                    if row.tax_rate and row.amount:
                        tax_breakdown.append(
                            {
                                "rate": float(row.tax_rate),
                                "amount": float(row.amount),
                            }
                        )

                # Get currency distribution
                currency_query = (
                    select(
                        ExtractedData.currency,
                        func.count(func.distinct(Invoice.id)).label("count"),
                    )
                    .select_from(Invoice)
                    .join(ExtractedData, Invoice.id == ExtractedData.invoice_id)
                    .where(
                        Invoice.processing_status == ProcessingStatus.COMPLETED,
                        ExtractedData.currency.isnot(None),
                    )
                    .group_by(ExtractedData.currency)
                    .order_by(func.count(func.distinct(Invoice.id)).desc())
                )

                currency_result = await session.execute(currency_query)
                currency_rows = currency_result.all()

                currency_distribution = []
                for row in currency_rows:
                    currency_distribution.append(
                        {
                            "currency": row.currency,
                            "count": row.count,
                        }
                    )

                await session.commit()

                return {
                    "total_amount": float(totals_row.total_amount) if totals_row.total_amount else 0.0,
                    "total_tax": float(totals_row.total_tax) if totals_row.total_tax else 0.0,
                    "tax_breakdown": tax_breakdown,
                    "currency_distribution": currency_distribution,
                }
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()

