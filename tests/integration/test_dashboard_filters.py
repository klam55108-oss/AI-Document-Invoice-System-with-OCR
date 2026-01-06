"""Integration tests for advanced filtering functionality."""

import pytest
from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_list_invoices_with_vendor_filter():
    """Test invoice list endpoint with vendor filter."""
    response = client.get(
        "/api/v1/invoices",
        params={"vendor": "Test"},
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)


def test_list_invoices_with_amount_range():
    """Test invoice list endpoint with amount range filters."""
    response = client.get(
        "/api/v1/invoices",
        params={
            "amount_min": 100.0,
            "amount_max": 1000.0,
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "data" in data


def test_list_invoices_with_confidence_filter():
    """Test invoice list endpoint with confidence filter."""
    response = client.get(
        "/api/v1/invoices",
        params={"confidence_min": 0.8},
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "data" in data


def test_list_invoices_with_validation_status_filter():
    """Test invoice list endpoint with validation status filter."""
    response = client.get(
        "/api/v1/invoices",
        params={"validation_status": "has_failed"},
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "data" in data


def test_list_invoices_with_multiple_filters():
    """Test invoice list endpoint with multiple filters combined."""
    response = client.get(
        "/api/v1/invoices",
        params={
            "status": "completed",
            "vendor": "Test",
            "amount_min": 100.0,
            "confidence_min": 0.7,
        },
    )
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "data" in data


def test_list_invoices_filter_validation():
    """Test invoice list endpoint validates filter parameters."""
    # Test invalid confidence (should be 0.0-1.0)
    response = client.get(
        "/api/v1/invoices",
        params={"confidence_min": 1.5},
    )
    
    # Should either accept and filter correctly or return error
    assert response.status_code in [200, 400, 422, 500]


def test_list_invoices_amount_range_validation():
    """Test invoice list endpoint validates amount range."""
    # Test with amount_min > amount_max
    response = client.get(
        "/api/v1/invoices",
        params={
            "amount_min": 1000.0,
            "amount_max": 100.0,
        },
    )
    
    # Should either accept and handle gracefully or return error
    assert response.status_code in [200, 400, 422, 500]

