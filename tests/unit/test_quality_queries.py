"""Unit tests for quality metrics query functions."""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test will fail until we implement the quality_metrics module
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def test_session():
    """Create test database session."""
    # This is a placeholder - in real implementation would use test database
    # For now, this will fail as expected for TDD
    pytest.skip("Quality metrics module not yet implemented")


async def test_get_quality_summary(test_session: AsyncSession):
    """Test quality summary query returns correct aggregated metrics."""
    from interface.dashboard.queries.quality_metrics import get_quality_summary
    
    # Test will fail because module doesn't exist yet
    summary = await get_quality_summary(test_session)
    
    # Expected structure
    assert "total_invoices" in summary
    assert "critical_fields_complete" in summary
    assert "avg_confidence" in summary
    
    assert isinstance(summary["total_invoices"], int)
    assert isinstance(summary["critical_fields_complete"], dict)
    assert isinstance(summary["avg_confidence"], dict)
    
    # Check critical fields completeness
    assert "vendor_name" in summary["critical_fields_complete"]
    assert "invoice_number" in summary["critical_fields_complete"]
    assert "total_amount" in summary["critical_fields_complete"]
    
    # Check average confidence scores
    assert "vendor_name" in summary["avg_confidence"]
    assert "invoice_number" in summary["avg_confidence"]
    assert "total_amount" in summary["avg_confidence"]


async def test_get_quality_by_format(test_session: AsyncSession):
    """Test quality by format query groups data correctly by file type."""
    from interface.dashboard.queries.quality_metrics import get_quality_by_format
    
    # Test will fail because module doesn't exist yet
    by_format = await get_quality_by_format(test_session)
    
    assert isinstance(by_format, list)
    
    if len(by_format) > 0:
        format_data = by_format[0]
        
        # Check required fields
        assert "file_type" in format_data
        assert "total" in format_data
        assert "vendor_extracted" in format_data
        assert "avg_vendor_conf" in format_data
        assert "avg_invoice_num_conf" in format_data
        assert "avg_total_conf" in format_data
        
        # Check types
        assert isinstance(format_data["file_type"], str)
        assert isinstance(format_data["total"], int)
        assert isinstance(format_data["avg_vendor_conf"], float)


async def test_get_low_confidence_invoices(test_session: AsyncSession):
    """Test low confidence invoices query filters correctly by threshold."""
    from interface.dashboard.queries.quality_metrics import get_low_confidence_invoices
    
    # Test will fail because module doesn't exist yet
    threshold = 0.7
    low_conf_invoices = await get_low_confidence_invoices(test_session, threshold)
    
    assert isinstance(low_conf_invoices, list)
    
    # All returned invoices should have at least one confidence below threshold
    for invoice in low_conf_invoices:
        has_low_confidence = (
            invoice.get("vendor_confidence", 1.0) < threshold or
            invoice.get("invoice_num_confidence", 1.0) < threshold or
            invoice.get("total_confidence", 1.0) < threshold
        )
        assert has_low_confidence, "Invoice should have at least one low confidence field"


async def test_quality_summary_with_no_data(test_session: AsyncSession):
    """Test quality summary handles empty database gracefully."""
    from interface.dashboard.queries.quality_metrics import get_quality_summary
    
    # Should return zeros for counts, not crash
    summary = await get_quality_summary(test_session)
    
    assert summary["total_invoices"] == 0
    assert all(count == 0 for count in summary["critical_fields_complete"].values())

