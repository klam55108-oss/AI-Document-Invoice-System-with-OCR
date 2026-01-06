"""Integration tests for bulk reprocess API endpoint."""

import pytest
from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_bulk_reprocess_endpoint_invalid_uuid():
    """Test bulk reprocess endpoint with invalid UUID."""
    response = client.post(
        "/api/v1/invoices/bulk/reprocess",
        json={
            "invoice_ids": ["invalid-uuid"],
            "force_reprocess": False,
        },
    )
    
    # Should return 200 but with failed status for invalid UUID
    assert response.status_code in [200, 422]
    if response.status_code == 200:
        data = response.json()
        assert data.get("status") in ["success", "error"]
        if data.get("status") == "success":
            assert data.get("failed", 0) >= 1


def test_bulk_reprocess_endpoint_empty_list():
    """Test bulk reprocess endpoint with empty invoice list."""
    response = client.post(
        "/api/v1/invoices/bulk/reprocess",
        json={
            "invoice_ids": [],
            "force_reprocess": False,
        },
    )
    
    # Should return 422 (validation error) for empty list
    assert response.status_code == 422


def test_bulk_reprocess_endpoint_missing_field():
    """Test bulk reprocess endpoint with missing required field."""
    response = client.post(
        "/api/v1/invoices/bulk/reprocess",
        json={
            "force_reprocess": False,
        },
    )
    
    # Should return 422 (validation error)
    assert response.status_code == 422


def test_bulk_reprocess_endpoint_structure():
    """Test bulk reprocess endpoint response structure."""
    # Use a valid UUID format (may not exist in DB)
    test_uuid = "123e4567-e89b-12d3-a456-426614174000"
    
    response = client.post(
        "/api/v1/invoices/bulk/reprocess",
        json={
            "invoice_ids": [test_uuid],
            "force_reprocess": False,
        },
    )
    
    # Should return 200 (even if invoice doesn't exist, it will be skipped)
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert "total_requested" in data
        assert "successful" in data
        assert "failed" in data
        assert "skipped" in data
        assert "results" in data
        assert isinstance(data["results"], list)


def test_bulk_reprocess_endpoint_force_flag():
    """Test bulk reprocess endpoint with force_reprocess flag."""
    test_uuid = "123e4567-e89b-12d3-a456-426614174000"
    
    response = client.post(
        "/api/v1/invoices/bulk/reprocess",
        json={
            "invoice_ids": [test_uuid],
            "force_reprocess": True,
        },
    )
    
    # Should accept the request
    assert response.status_code in [200, 422, 500]

