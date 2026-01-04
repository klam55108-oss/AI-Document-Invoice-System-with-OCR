"""Unit tests for validation rules."""

from decimal import Decimal

import pytest

from brain.schemas import ExtractedDataSchema
from brain.validator import MathCheckSubtotalTaxRule, ValidationFramework


@pytest.mark.asyncio
async def test_math_check_subtotal_tax_passed():
    """Test math validation when calculation is correct."""
    rule = MathCheckSubtotalTaxRule()

    extracted_data = ExtractedDataSchema(
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1100.00"),
    )

    result = await rule.validate(extracted_data)

    assert result.status == "passed"
    assert result.rule_name == "math_check_subtotal_tax"
    assert result.expected_value == Decimal("1100.00")
    assert result.actual_value == Decimal("1100.00")
    assert result.error_message is None


@pytest.mark.asyncio
async def test_math_check_subtotal_tax_failed():
    """Test math validation when calculation is incorrect."""
    rule = MathCheckSubtotalTaxRule()

    extracted_data = ExtractedDataSchema(
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1200.00"),  # Wrong total
    )

    result = await rule.validate(extracted_data)

    assert result.status == "failed"
    assert result.expected_value == Decimal("1100.00")
    assert result.actual_value == Decimal("1200.00")
    assert result.error_message is not None
    assert "exceeds tolerance" in result.error_message


@pytest.mark.asyncio
async def test_math_check_within_tolerance():
    """Test math validation with small difference within tolerance."""
    rule = MathCheckSubtotalTaxRule(tolerance=Decimal("0.01"))

    extracted_data = ExtractedDataSchema(
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1100.01"),  # 1 cent difference
    )

    result = await rule.validate(extracted_data)

    assert result.status == "passed"  # Within tolerance


@pytest.mark.asyncio
async def test_math_check_missing_fields():
    """Test math validation when required fields are missing."""
    rule = MathCheckSubtotalTaxRule()

    extracted_data = ExtractedDataSchema(
        subtotal=Decimal("1000.00"),
        # tax_amount and total_amount missing
    )

    result = await rule.validate(extracted_data)

    assert result.status == "warning"
    assert "Missing required fields" in result.error_message


@pytest.mark.asyncio
async def test_validation_framework():
    """Test validation framework runs all rules."""
    framework = ValidationFramework()

    extracted_data = ExtractedDataSchema(
        subtotal=Decimal("1000.00"),
        tax_amount=Decimal("100.00"),
        total_amount=Decimal("1100.00"),
    )

    results = await framework.validate(extracted_data)

    assert len(results) >= 1
    assert any(r.rule_name == "math_check_subtotal_tax" for r in results)


@pytest.mark.asyncio
async def test_validation_framework_add_rule():
    """Test adding custom validation rule."""
    framework = ValidationFramework()
    initial_count = len(framework.rules)

    # Create a simple custom rule
    class CustomRule(MathCheckSubtotalTaxRule):
        def __init__(self):
            super().__init__()
            self.name = "custom_rule"

    framework.add_rule(CustomRule())

    assert len(framework.rules) == initial_count + 1

