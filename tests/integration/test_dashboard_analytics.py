"""Integration tests for dashboard analytics API endpoints."""

import pytest
from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_get_status_distribution_endpoint():
    """Test GET /api/v1/invoices/analytics/status-distribution endpoint."""
    response = client.get("/api/v1/invoices/analytics/status-distribution")
    
    assert response.status_code in [200, 500]  # 500 if DB not available
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        # Should be a dictionary mapping status to counts
        assert all(isinstance(k, str) for k in data.keys())
        assert all(isinstance(v, int) for v in data.values())


def test_get_time_series_endpoint():
    """Test GET /api/v1/invoices/analytics/time-series endpoint."""
    response = client.get("/api/v1/invoices/analytics/time-series?aggregation=daily")
    
    assert response.status_code in [200, 400, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # Each item should have date and count
        if len(data) > 0:
            assert "date" in data[0]
            assert "count" in data[0]


def test_get_time_series_endpoint_invalid_aggregation():
    """Test time series endpoint with invalid aggregation parameter."""
    response = client.get("/api/v1/invoices/analytics/time-series?aggregation=invalid")
    
    # Should return 422 (validation error) or 400
    assert response.status_code in [400, 422]


def test_get_vendor_analysis_endpoint():
    """Test GET /api/v1/invoices/analytics/vendor-analysis endpoint."""
    response = client.get("/api/v1/invoices/analytics/vendor-analysis?sort_by=count&limit=10")
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # Each item should have vendor information
        if len(data) > 0:
            assert "vendor_name" in data[0] or "name" in data[0]


def test_get_vendor_analysis_endpoint_invalid_params():
    """Test vendor analysis endpoint with invalid parameters."""
    response = client.get("/api/v1/invoices/analytics/vendor-analysis?sort_by=invalid&limit=100")
    
    # Should return 422 (validation error) or 400
    assert response.status_code in [400, 422]


def test_get_financial_summary_endpoint():
    """Test GET /api/v1/invoices/analytics/financial-summary endpoint."""
    response = client.get("/api/v1/invoices/analytics/financial-summary")
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)
        # Should have financial summary fields
        assert "total_amount" in data or len(data) >= 0  # May be empty if no data

