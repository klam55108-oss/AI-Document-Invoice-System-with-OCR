"""Integration tests for validation pipeline."""

from decimal import Decimal

import pytest

from brain.schemas import ExtractedDataSchema
from brain.validator import ValidationFramework


@pytest.mark.asyncio
async def test_validation_pipeline_end_to_end():
    """Test complete validation pipeline with extracted data."""
    framework = ValidationFramework()

    # Valid invoice data
    valid_data = ExtractedDataSchema(
        vendor_name="Test Vendor",
        invoice_number="INV-001",
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1100.00"),
        currency="USD",
    )

    results = await framework.validate(valid_data)

    # Should have at least one validation result
    assert len(results) > 0

    # Math check should pass
    math_result = next((r for r in results if r.rule_name == "math_check_subtotal_tax"), None)
    assert math_result is not None
    assert math_result.status == "passed"


@pytest.mark.asyncio
async def test_validation_pipeline_with_errors():
    """Test validation pipeline with invalid data."""
    framework = ValidationFramework()

    # Invalid invoice data (math doesn't add up)
    invalid_data = ExtractedDataSchema(
        vendor_name="Test Vendor",
        invoice_number="INV-002",
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1500.00"),  # Wrong total
        currency="USD",
    )

    results = await framework.validate(invalid_data)

    # Math check should fail
    math_result = next((r for r in results if r.rule_name == "math_check_subtotal_tax"), None)
    assert math_result is not None
    assert math_result.status == "failed"
    assert math_result.error_message is not None


@pytest.mark.asyncio
async def test_validation_pipeline_partial_data():
    """Test validation pipeline with partial data."""
    framework = ValidationFramework()

    # Partial data (missing amounts)
    partial_data = ExtractedDataSchema(
        vendor_name="Test Vendor",
        invoice_number="INV-003",
        # Missing subtotal, tax, total
    )

    results = await framework.validate(partial_data)

    # Should still run validations (may return warnings)
    assert len(results) > 0

