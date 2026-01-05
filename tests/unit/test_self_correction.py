"""Unit tests for self-correction refinement logic."""

import pytest
from decimal import Decimal
from datetime import date
from brain.schemas import ExtractedDataSchema, ValidationRuleResult
from brain.extractor import refine_extraction

@pytest.mark.asyncio
async def test_refine_extraction_simulated():
    """Test refinement loop simulation."""
    previous_data = ExtractedDataSchema(
        vendor_name="Test Vendor",
        subtotal=Decimal("100.00"),
        tax_amount=Decimal("10.00"),
        total_amount=Decimal("120.00"),  # Fails math check
        extraction_confidence=Decimal("0.3")
    )

    validation_errors = [
        ValidationRuleResult(
            rule_name="math_check_subtotal_tax",
            status="failed",
            error_message="100 + 10 != 120"
        )
    ]

    refined = await refine_extraction("Raw text contents...", previous_data, validation_errors)

    assert refined.extraction_confidence > previous_data.extraction_confidence
    assert refined.vendor_name == previous_data.vendor_name
