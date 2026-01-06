"""Analytics route handlers for dashboard visualizations."""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query

from interface.dashboard.queries import (
    get_financial_summary_data,
    get_status_distribution,
    get_time_series_data,
    get_vendor_analysis_data,
)

router = APIRouter(prefix="/api/v1/invoices/analytics", tags=["Analytics"])


@router.get("/status-distribution")
async def get_status_distribution_endpoint() -> dict[str, int]:
    """Get invoice processing status distribution for charts.

    Returns:
        Dictionary mapping status names to counts
        Example: {"completed": 150, "failed": 10, "processing": 5}
    """
    try:
        return await get_status_distribution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching status distribution: {str(e)}")


@router.get("/time-series")
async def get_time_series_endpoint(
    aggregation: Annotated[
        str,
        Query(
            description="Time aggregation level",
            pattern="^(daily|weekly|monthly)$",
        ),
    ] = "daily",
    start_date: Annotated[str | None, Query(description="Start date (YYYY-MM-DD)")] = None,
    end_date: Annotated[str | None, Query(description="End date (YYYY-MM-DD)")] = None,
) -> list[dict[str, Any]]:
    """Get time series data for processing volume trends.

    Args:
        aggregation: Time aggregation level ("daily", "weekly", "monthly")
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)

    Returns:
        List of dictionaries with "date" and "count" keys
    """
    from datetime import date as date_type

    start = None
    end = None

    if start_date:
        try:
            start = date_type.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid start_date format: {start_date}. Use YYYY-MM-DD")

    if end_date:
        try:
            end = date_type.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid end_date format: {end_date}. Use YYYY-MM-DD")

    try:
        return await get_time_series_data(aggregation=aggregation, start_date=start, end_date=end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching time series data: {str(e)}")


@router.get("/vendor-analysis")
async def get_vendor_analysis_endpoint(
    sort_by: Annotated[
        str,
        Query(
            description="Sort by count or amount",
            pattern="^(count|amount)$",
        ),
    ] = "count",
    limit: Annotated[int, Query(ge=1, le=50, description="Number of top vendors")] = 10,
) -> list[dict[str, Any]]:
    """Get vendor analysis data for charts.

    Args:
        sort_by: Sort by "count" or "amount"
        limit: Number of top vendors to return (1-50)

    Returns:
        List of dictionaries with vendor information
    """
    try:
        return await get_vendor_analysis_data(sort_by=sort_by, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vendor analysis: {str(e)}")


@router.get("/financial-summary")
async def get_financial_summary_endpoint() -> dict[str, Any]:
    """Get financial summary data for charts.

    Returns:
        Dictionary with financial aggregates including total amount, tax breakdown, and currency distribution
    """
    try:
        return await get_financial_summary_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching financial summary: {str(e)}")

