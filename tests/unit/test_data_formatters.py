"""Unit tests for data formatting utilities."""

from decimal import Decimal

import pytest

from interface.dashboard.utils.data_formatters import (
    EnhancedValidationResult,
    MissingDataInfo,
    enhance_validation_result,
    format_missing_field,
)


def test_format_missing_field_present() -> None:
    """Test formatting when field is present."""
    result = format_missing_field("subtotal", Decimal("100.00"), Decimal("0.95"))

    assert result["is_missing"] is False
    assert result["reason"] is None
    assert result["confidence"] == Decimal("0.95")


def test_format_missing_field_missing() -> None:
    """Test formatting when field is missing."""
    result = format_missing_field("subtotal", None)

    assert result["is_missing"] is True
    assert result["reason"] == "Not found in invoice"
    assert result["field_name"] == "subtotal"


def test_format_missing_field_low_confidence() -> None:
    """Test formatting when field has low confidence."""
    result = format_missing_field("vendor_name", None, Decimal("0.4"))

    assert result["is_missing"] is True
    assert "low confidence" in result["reason"].lower() or "extraction failed" in result["reason"].lower()


def test_format_missing_field_financial_specific() -> None:
    """Test formatting for financial fields with specific reasons."""
    result = format_missing_field("tax_amount", None, field_type="financial")

    assert result["is_missing"] is True
    assert result["reason"] is not None
    assert "not found" in result["reason"].lower()


def test_enhance_validation_result_failed() -> None:
    """Test enhancing a failed validation result."""
    result = enhance_validation_result(
        rule_name="math_check_subtotal_tax",
        rule_description="Check that subtotal + tax = total",
        status="failed",
        expected_value=Decimal("110.00"),
        actual_value=Decimal("100.00"),
        error_message="Calculation mismatch",
    )

    assert result["severity"] == "error"
    assert result["actionable"] is True
    assert result["suggested_action"] is not None
    assert result["display_priority"] == 1
    assert result["status"] == "failed"


def test_enhance_validation_result_warning() -> None:
    """Test enhancing a warning validation result."""
    result = enhance_validation_result(
        rule_name="date_consistency",
        rule_description="Check invoice date is before due date",
        status="warning",
        error_message="Dates are close",
    )

    assert result["severity"] == "warning"
    assert result["actionable"] is True
    assert result["display_priority"] == 2
    assert result["status"] == "warning"


def test_enhance_validation_result_passed() -> None:
    """Test enhancing a passed validation result."""
    result = enhance_validation_result(
        rule_name="vendor_sanity",
        rule_description="Check vendor name exists",
        status="passed",
    )

    assert result["severity"] == "info"
    assert result["actionable"] is False
    assert result["suggested_action"] is None
    assert result["display_priority"] == 3
    assert result["status"] == "passed"


def test_enhance_validation_result_math_rule_suggestion() -> None:
    """Test that math rules get appropriate suggested action."""
    result = enhance_validation_result(
        rule_name="math_check",
        rule_description="Math validation",
        status="failed",
        error_message="Math error",
    )

    assert "calculation" in result["suggested_action"].lower() or "reprocess" in result["suggested_action"].lower()


def test_enhance_validation_result_date_rule_suggestion() -> None:
    """Test that date rules get appropriate suggested action."""
    result = enhance_validation_result(
        rule_name="date_check",
        rule_description="Date validation",
        status="failed",
        error_message="Date error",
    )

    assert "date" in result["suggested_action"].lower()


def test_enhance_validation_result_vendor_rule_suggestion() -> None:
    """Test that vendor rules get appropriate suggested action."""
    result = enhance_validation_result(
        rule_name="vendor_check",
        rule_description="Vendor validation",
        status="failed",
        error_message="Vendor error",
    )

    assert "vendor" in result["suggested_action"].lower()

