"""Quality metrics API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from core.database import get_session
from interface.dashboard.queries import (
    get_quality_summary,
    get_quality_by_format,
    get_low_confidence_invoices,
)
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("/metrics")
async def get_quality_metrics(
    session: AsyncSession = Depends(get_session),
    date_from: Optional[date] = Query(None, description="Filter invoices from this date"),
    date_to: Optional[date] = Query(None, description="Filter invoices until this date"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    group_by: Optional[str] = Query("file_type", description="Grouping dimension"),
):
    """Get aggregated quality metrics for the dashboard.
    
    Returns quality metrics including:
    - Overall summary (total invoices, completion rates, average confidence)
    - Metrics grouped by file format
    - Missing fields breakdown
    - Low confidence invoices
    
    Query Parameters:
        date_from: Start date for filtering (ISO 8601 format)
        date_to: End date for filtering (ISO 8601 format)
        file_type: Filter by specific file type (pdf, csv, xlsx, jpg, png, etc.)
        group_by: Grouping dimension (file_type, date, category, group)
    
    Returns:
        JSON response with quality metrics
    """
    logger.info(
        "Quality metrics API called",
        date_from=date_from,
        date_to=date_to,
        file_type=file_type,
        group_by=group_by,
    )
    
    # Fetch metrics (filters will be implemented in future enhancement)
    summary = await get_quality_summary(session)
    by_format = await get_quality_by_format(session)
    low_confidence = await get_low_confidence_invoices(session, confidence_threshold=0.7)
    
    # Calculate additional metrics
    failed_invoices = summary["total_invoices"] - summary["critical_fields_complete"]["vendor_name"]
    completed_invoices = summary["critical_fields_complete"]["vendor_name"]
    
    # Calculate overall accuracy (% of invoices with all critical fields)
    overall_accuracy = 0.0
    if summary["total_invoices"] > 0:
        all_fields_complete = min(
            summary["critical_fields_complete"]["vendor_name"],
            summary["critical_fields_complete"]["invoice_number"],
            summary["critical_fields_complete"]["total_amount"],
        )
        overall_accuracy = all_fields_complete / summary["total_invoices"]
    
    # Calculate STP rate (invoices with high confidence and all fields)
    stp_count = sum(
        1 for inv in low_confidence
        if all([
            (inv.get("vendor_confidence") or 0) >= 0.7,
            (inv.get("invoice_num_confidence") or 0) >= 0.7,
            (inv.get("total_confidence") or 0) >= 0.7,
        ])
    )
    stp_rate = 1.0 - (len(low_confidence) / summary["total_invoices"]) if summary["total_invoices"] > 0 else 0.0
    
    # Build response
    response_data = {
        "summary": {
            "total_invoices": summary["total_invoices"],
            "completed_invoices": completed_invoices,
            "failed_invoices": failed_invoices,
            "overall_accuracy": round(overall_accuracy, 2),
            "stp_rate": round(stp_rate, 2),
        },
        "by_format": [
            {
                "file_type": item["file_type"],
                "total": item["total"],
                "critical_fields_complete_pct": round(
                    item["vendor_extracted"] / item["total"] if item["total"] > 0 else 0, 2
                ),
                "avg_vendor_confidence": round(item["avg_vendor_conf"], 2),
                "avg_invoice_number_confidence": round(item["avg_invoice_num_conf"], 2),
                "avg_total_amount_confidence": round(item["avg_total_conf"], 2),
            }
            for item in by_format
        ],
        "missing_fields": {
            "vendor_name_missing": summary["total_invoices"] - summary["critical_fields_complete"]["vendor_name"],
            "invoice_number_missing": summary["total_invoices"] - summary["critical_fields_complete"]["invoice_number"],
            "total_amount_missing": summary["total_invoices"] - summary["critical_fields_complete"]["total_amount"],
        },
        "low_confidence_invoices": {
            "count": len(low_confidence),
            "percentage": round(len(low_confidence) / summary["total_invoices"], 2) if summary["total_invoices"] > 0 else 0.0,
        },
    }
    
    # Add date range if filtered
    if date_from or date_to:
        response_data["date_range"] = {
            "from": str(date_from) if date_from else None,
            "to": str(date_to) if date_to else None,
        }
    
    logger.info(
        "Quality metrics returned",
        total=summary["total_invoices"],
        accuracy=overall_accuracy,
    )
    
    return {
        "status": "success",
        "data": response_data,
    }


@router.get("/trends")
async def get_quality_trends(
    session: AsyncSession = Depends(get_session),
    date_from: date = Query(..., description="Start date for trend data"),
    date_to: date = Query(..., description="End date for trend data"),
    granularity: str = Query("day", description="Time granularity (day, week, month)"),
    metric: str = Query("all", description="Specific metric (accuracy, confidence, stp_rate, all)"),
):
    """Get quality metrics trends over time.
    
    Returns time-series data for quality metrics to display trend charts.
    
    Query Parameters:
        date_from: Start date (required)
        date_to: End date (required)
        granularity: Time granularity (day, week, month)
        metric: Specific metric to retrieve (accuracy, confidence, stp_rate, all)
    
    Returns:
        JSON response with trend data
    """
    logger.info(
        "Quality trends API called",
        date_from=date_from,
        date_to=date_to,
        granularity=granularity,
        metric=metric,
    )
    
    # TODO: Implement time-series aggregation
    # For now, return placeholder structure
    response_data = {
        "date_range": {
            "from": str(date_from),
            "to": str(date_to),
        },
        "granularity": granularity,
        "series": [
            {
                "metric": "overall_accuracy",
                "label": "Overall Extraction Accuracy",
                "data_points": [],
            }
        ],
    }
    
    logger.info("Quality trends placeholder returned")
    
    return {
        "status": "success",
        "data": response_data,
    }

