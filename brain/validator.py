"""Validation rules for invoice data consistency."""

from decimal import Decimal
from typing import Any

from brain.schemas import ExtractedDataSchema, ValidationRuleResult
from core.logging import get_logger

logger = get_logger(__name__)

# Default tolerance for mathematical checks (1 cent)
DEFAULT_TOLERANCE = Decimal("0.01")


class ValidationRule:
    """Base class for validation rules."""

    def __init__(self, name: str, description: str | None = None):
        """Initialize validation rule.

        Args:
            name: Rule identifier
            description: Human-readable description
        """
        self.name = name
        self.description = description

    async def validate(self, extracted_data: ExtractedDataSchema) -> ValidationRuleResult:
        """Validate extracted data against this rule.

        Args:
            extracted_data: Extracted invoice data to validate

        Returns:
            ValidationRuleResult with validation outcome
        """
        raise NotImplementedError("Subclasses must implement validate method")


class MathCheckSubtotalTaxRule(ValidationRule):
    """Validates that subtotal + tax_amount = total_amount (within tolerance)."""

    def __init__(self, tolerance: Decimal = DEFAULT_TOLERANCE):
        """Initialize math check rule.

        Args:
            tolerance: Allowed difference in calculation (default: 0.01)
        """
        super().__init__(
            name="math_check_subtotal_tax",
            description="Validates that subtotal + tax equals total amount",
        )
        self.tolerance = tolerance

    async def validate(self, extracted_data: ExtractedDataSchema) -> ValidationRuleResult:
        """Validate subtotal + tax = total.

        Args:
            extracted_data: Extracted invoice data

        Returns:
            ValidationRuleResult with validation outcome
        """
        # Check if required fields are present
        if extracted_data.subtotal is None or extracted_data.tax_amount is None or extracted_data.total_amount is None:
            return ValidationRuleResult(
                rule_name=self.name,
                rule_description=self.description,
                status="warning",
                error_message="Missing required fields for math validation (subtotal, tax_amount, or total_amount)",
            )

        # Calculate expected total
        expected_total = extracted_data.subtotal + extracted_data.tax_amount
        actual_total = extracted_data.total_amount

        # Calculate difference
        difference = abs(expected_total - actual_total)

        # Check if within tolerance
        if difference <= self.tolerance:
            logger.debug(
                "Math validation passed",
                rule=self.name,
                expected=expected_total,
                actual=actual_total,
                difference=difference,
            )
            return ValidationRuleResult(
                rule_name=self.name,
                rule_description=self.description,
                status="passed",
                expected_value=expected_total,
                actual_value=actual_total,
                tolerance=self.tolerance,
            )
        else:
            logger.warning(
                "Math validation failed",
                rule=self.name,
                expected=expected_total,
                actual=actual_total,
                difference=difference,
                tolerance=self.tolerance,
            )
            return ValidationRuleResult(
                rule_name=self.name,
                rule_description=self.description,
                status="failed",
                expected_value=expected_total,
                actual_value=actual_total,
                tolerance=self.tolerance,
                error_message=f"Subtotal ({extracted_data.subtotal}) + Tax ({extracted_data.tax_amount}) = {expected_total}, but Total is {actual_total}. Difference: {difference} exceeds tolerance: {self.tolerance}",
            )


class ValidationFramework:
    """Framework for running validation rules."""

    def __init__(self):
        """Initialize validation framework with default rules."""
        self.rules: list[ValidationRule] = [
            MathCheckSubtotalTaxRule(),
        ]

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule.

        Args:
            rule: ValidationRule instance to add
        """
        self.rules.append(rule)
        logger.info("Validation rule added", rule_name=rule.name)

    async def validate(self, extracted_data: ExtractedDataSchema) -> list[ValidationRuleResult]:
        """Run all validation rules on extracted data.

        Args:
            extracted_data: Extracted invoice data to validate

        Returns:
            List of ValidationRuleResult for each rule
        """
        results = []

        for rule in self.rules:
            try:
                result = await rule.validate(extracted_data)
                results.append(result)
                logger.debug("Validation rule executed", rule=rule.name, status=result.status)
            except Exception as e:
                logger.error("Validation rule failed", rule=rule.name, error=str(e))
                # Create error result
                results.append(
                    ValidationRuleResult(
                        rule_name=rule.name,
                        rule_description=rule.description,
                        status="failed",
                        error_message=f"Validation rule execution failed: {str(e)}",
                    )
                )

        return results


# Global validation framework instance
_validation_framework: ValidationFramework | None = None


def get_validation_framework() -> ValidationFramework:
    """Get the global validation framework instance."""
    global _validation_framework
    if _validation_framework is None:
        _validation_framework = ValidationFramework()
    return _validation_framework

