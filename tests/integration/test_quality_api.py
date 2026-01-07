"""Integration tests for quality metrics API endpoints."""

import pytest
from httpx import AsyncClient
from fastapi import status

# Test will fail until we implement the quality API endpoints
pytestmark = pytest.mark.asyncio


async def test_get_quality_metrics_success(client_with_db: AsyncClient):
    """Test GET /api/v1/quality/metrics returns quality data."""
    # Test will fail because endpoint doesn't exist yet
    response = await client_with_db.get("/api/v1/quality/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    
    data = response.json()
    assert "status" in data
    assert data["status"] == "success"
    assert "data" in data
    
    metrics = data["data"]
    assert "summary" in metrics
    assert "by_format" in metrics
    assert "missing_fields" in metrics
    assert "low_confidence_invoices" in metrics


async def test_get_quality_metrics_with_filters(client_with_db: AsyncClient):
    """Test quality metrics API with date range filters."""
    # Test will fail because endpoint doesn't exist yet
    response = await client_with_db.get(
        "/api/v1/quality/metrics",
        params={
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "file_type": "pdf"
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Should return filtered data
    assert data["status"] == "success"
    assert "date_range" in data["data"]


async def test_get_quality_metrics_invalid_date_format(client_with_db: AsyncClient):
    """Test quality metrics API rejects invalid date format."""
    # Test will fail because endpoint doesn't exist yet
    response = await client_with_db.get(
        "/api/v1/quality/metrics",
        params={"date_from": "invalid-date"}
    )
    
    # Should return 400 Bad Request or 422 Validation Error
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


async def test_quality_metrics_returns_correct_structure(client_with_db: AsyncClient):
    """Test quality metrics response has correct structure."""
    # Test will fail because endpoint doesn't exist yet
    response = await client_with_db.get("/api/v1/quality/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    
    # Check summary structure
    assert "total_invoices" in data["summary"]
    assert "completed_invoices" in data["summary"]
    assert "overall_accuracy" in data["summary"]
    
    # Check by_format structure
    if len(data["by_format"]) > 0:
        format_item = data["by_format"][0]
        assert "file_type" in format_item
        assert "total" in format_item
        assert "avg_vendor_confidence" in format_item
        assert "avg_invoice_number_confidence" in format_item
        assert "avg_total_amount_confidence" in format_item


async def test_quality_metrics_with_no_data(client_with_db: AsyncClient):
    """Test quality metrics handles empty database gracefully."""
    # Test will fail because endpoint doesn't exist yet
    response = await client_with_db.get("/api/v1/quality/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    
    # Should return zeros, not crash
    assert data["summary"]["total_invoices"] >= 0

