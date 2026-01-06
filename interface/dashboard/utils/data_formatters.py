"""Data formatting utilities for missing data and validation results."""

from decimal import Decimal
from typing import TypedDict, Any


class MissingDataInfo(TypedDict, total=False):
    """Information about missing data fields."""

    field_name: str
    is_missing: bool
    reason: str | None
    confidence: Decimal | None
    alternative_value: Any | None


class EnhancedValidationResult(TypedDict, total=False):
    """Enhanced validation result with display metadata."""

    # Original ValidationResult fields
    rule_name: str
    rule_description: str | None
    status: str  # "passed", "failed", "warning"
    expected_value: Decimal | None
    actual_value: Decimal | None
    tolerance: Decimal | None
    error_message: str | None

    # Enhanced fields
    severity: str  # "error", "warning", "info"
    actionable: bool
    suggested_action: str | None
    display_priority: int  # Lower = higher priority


def format_missing_field(
    field_name: str,
    value: Any | None,
    confidence: Decimal | None = None,
    field_type: str = "financial",
) -> MissingDataInfo:
    """Format missing field information with appropriate reason.

    Args:
        field_name: Name of the field (e.g., "subtotal", "tax_amount")
        value: Field value (None indicates missing)
        confidence: Optional extraction confidence score
        field_type: Type of field ("financial", "date", "text", etc.)

    Returns:
        MissingDataInfo dictionary with field status and explanation
    """
    if value is not None:
        # Field is present
        return MissingDataInfo(
            field_name=field_name,
            is_missing=False,
            reason=None,
            confidence=confidence,
            alternative_value=None,
        )

    # Field is missing - determine reason
    reason = "Not found in invoice"
    if confidence is not None and confidence < Decimal("0.5"):
        reason = "Extraction failed (low confidence)"
    elif confidence is not None and confidence < Decimal("0.8"):
        reason = "Low confidence extraction"

    # Field-specific reasons
    if field_type == "financial":
        if field_name in ("subtotal", "tax_amount"):
            reason = "Not found in invoice (field may not be present in this invoice format)"

    return MissingDataInfo(
        field_name=field_name,
        is_missing=True,
        reason=reason,
        confidence=confidence,
        alternative_value=None,
    )


def enhance_validation_result(
    rule_name: str,
    rule_description: str | None,
    status: str,
    expected_value: Decimal | None = None,
    actual_value: Decimal | None = None,
    tolerance: Decimal | None = None,
    error_message: str | None = None,
) -> EnhancedValidationResult:
    """Enhance validation result with display metadata.

    Args:
        rule_name: Name of the validation rule
        rule_description: Description of what the rule checks
        status: Validation status ("passed", "failed", "warning")
        expected_value: Expected value for the validation
        actual_value: Actual value found
        tolerance: Allowed tolerance for numeric comparisons
        error_message: Error message if validation failed

    Returns:
        EnhancedValidationResult with severity, actionable flag, and display priority
    """
    status_lower = status.lower()

    # Determine severity
    if status_lower == "failed":
        severity = "error"
        actionable = True
        suggested_action = "Review invoice and reprocess if needed"
        display_priority = 1
    elif status_lower == "warning":
        severity = "warning"
        actionable = True
        suggested_action = "Verify data accuracy"
        display_priority = 2
    else:  # passed
        severity = "info"
        actionable = False
        suggested_action = None
        display_priority = 3

    # Customize suggested action based on rule type
    if error_message:
        if "math" in rule_name.lower() or "calculation" in rule_name.lower():
            suggested_action = "Check invoice calculations and reprocess"
        elif "date" in rule_name.lower():
            suggested_action = "Verify invoice dates are correct"
        elif "vendor" in rule_name.lower():
            suggested_action = "Verify vendor information"

    return EnhancedValidationResult(
        rule_name=rule_name,
        rule_description=rule_description,
        status=status,
        expected_value=expected_value,
        actual_value=actual_value,
        tolerance=tolerance,
        error_message=error_message,
        severity=severity,
        actionable=actionable,
        suggested_action=suggested_action,
        display_priority=display_priority,
    )

