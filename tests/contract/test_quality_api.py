"""Contract tests for quality metrics API - validates API contract compliance."""

import pytest
from httpx import AsyncClient
from fastapi import status
from pydantic import BaseModel, Field, ValidationError

# Test will fail until we implement the quality API endpoints
pytestmark = pytest.mark.asyncio


# Contract schemas based on contracts/extraction-api.yaml
class QualityMetricsSummary(BaseModel):
    """Contract schema for quality metrics summary."""
    total_invoices: int
    completed_invoices: int
    failed_invoices: int
    overall_accuracy: float = Field(ge=0, le=1)
    stp_rate: float = Field(ge=0, le=1)


class FormatMetrics(BaseModel):
    """Contract schema for format-specific metrics."""
    file_type: str
    total: int
    critical_fields_complete_pct: float = Field(ge=0, le=1)
    avg_vendor_confidence: float = Field(ge=0, le=1)
    avg_invoice_number_confidence: float = Field(ge=0, le=1)
    avg_total_amount_confidence: float = Field(ge=0, le=1)


class QualityMetricsResponse(BaseModel):
    """Contract schema for quality metrics response."""
    status: str
    timestamp: str
    data: dict  # Will validate structure in test


@pytest.fixture
async def client():
    """Create test HTTP client."""
    from interface.api.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_quality_metrics_contract_response_structure(client: AsyncClient):
    """Test quality metrics API response matches contract specification."""
    # Test will fail because endpoint doesn't exist yet
    response = await client.get("/api/v1/quality/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    
    # Validate response matches contract
    try:
        response_data = QualityMetricsResponse(**response.json())
        assert response_data.status == "success"
        assert response_data.timestamp is not None
    except ValidationError as e:
        pytest.fail(f"Response does not match contract: {e}")


async def test_quality_metrics_contract_summary_fields(client: AsyncClient):
    """Test summary section matches contract specification."""
    # Test will fail because endpoint doesn't exist yet
    response = await client.get("/api/v1/quality/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    
    # Validate summary matches contract
    try:
        summary = QualityMetricsSummary(**data["summary"])
        
        # Validate ranges
        assert 0 <= summary.overall_accuracy <= 1
        assert 0 <= summary.stp_rate <= 1
        assert summary.total_invoices >= 0
        assert summary.completed_invoices >= 0
        assert summary.failed_invoices >= 0
        
    except ValidationError as e:
        pytest.fail(f"Summary does not match contract: {e}")


async def test_quality_metrics_contract_format_fields(client: AsyncClient):
    """Test by_format section matches contract specification."""
    # Test will fail because endpoint doesn't exist yet
    response = await client.get("/api/v1/quality/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    
    # Validate each format item matches contract
    for format_item in data.get("by_format", []):
        try:
            format_metrics = FormatMetrics(**format_item)
            
            # Validate file type is supported
            assert format_metrics.file_type in ["pdf", "csv", "xlsx", "jpg", "png", "webp", "avif"]
            
            # Validate confidence ranges
            assert 0 <= format_metrics.avg_vendor_confidence <= 1
            assert 0 <= format_metrics.avg_invoice_number_confidence <= 1
            assert 0 <= format_metrics.avg_total_amount_confidence <= 1
            assert 0 <= format_metrics.critical_fields_complete_pct <= 1
            
        except ValidationError as e:
            pytest.fail(f"Format metrics do not match contract: {e}")


async def test_quality_metrics_contract_query_parameters(client: AsyncClient):
    """Test API accepts query parameters per contract specification."""
    # Test will fail because endpoint doesn't exist yet
    
    # According to contract, should accept date_from, date_to, file_type, group_by
    response = await client.get(
        "/api/v1/quality/metrics",
        params={
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "file_type": "pdf",
            "group_by": "file_type"
        }
    )
    
    # Should either succeed or return 422 if parameters are invalid
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "data" in data


async def test_quality_metrics_contract_error_response(client: AsyncClient):
    """Test error responses match contract specification."""
    # Test will fail because endpoint doesn't exist yet
    
    # Try invalid date format
    response = await client.get(
        "/api/v1/quality/metrics",
        params={"date_from": "not-a-date"}
    )
    
    # Should return error response per contract
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    error_data = response.json()
    # Per contract, error response should have status="error" and error object
    assert "status" in error_data or "detail" in error_data  # FastAPI returns "detail" for validation errors

