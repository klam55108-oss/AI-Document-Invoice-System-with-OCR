"""Filter utilities for dashboard invoice filtering."""

from typing import Any


def validate_filter_state(filters: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate filter state for consistency.

    Args:
        filters: Dictionary containing filter parameters:
            - amount_min: Minimum amount (optional)
            - amount_max: Maximum amount (optional)
            - confidence_min: Minimum confidence (optional, 0.0-1.0)
            - vendor: Vendor name filter (optional)
            - validation_status: Validation status filter (optional)

    Returns:
        Tuple of (is_valid, error_message)
        If valid, returns (True, None)
        If invalid, returns (False, error_message)
    """
    # Validate amount range
    amount_min = filters.get("amount_min")
    amount_max = filters.get("amount_max")
    
    if amount_min is not None and amount_max is not None:
        if amount_min < 0:
            return False, "Minimum amount cannot be negative"
        if amount_max < 0:
            return False, "Maximum amount cannot be negative"
        if amount_min > amount_max:
            return False, "Minimum amount must be less than or equal to maximum amount"
    
    # Validate confidence range
    confidence_min = filters.get("confidence_min")
    if confidence_min is not None:
        if not isinstance(confidence_min, (int, float)):
            return False, "Confidence must be a number"
        if confidence_min < 0.0 or confidence_min > 1.0:
            return False, "Confidence must be between 0.0 and 1.0"
    
    return True, None


def apply_filters_to_query(query, filters: dict[str, Any], ExtractedData, Invoice):
    """Apply filter conditions to SQLAlchemy query.

    Args:
        query: SQLAlchemy select query
        filters: Dictionary of filter parameters
        ExtractedData: ExtractedData model class
        Invoice: Invoice model class

    Returns:
        Modified query with filter conditions applied
    """
    # Vendor filter
    if filters.get("vendor"):
        vendor_pattern = f"%{filters['vendor']}%"
        query = query.where(ExtractedData.vendor_name.ilike(vendor_pattern))
    
    # Amount range filter
    amount_min = filters.get("amount_min")
    amount_max = filters.get("amount_max")
    if amount_min is not None:
        query = query.where(ExtractedData.total_amount >= amount_min)
    if amount_max is not None:
        query = query.where(ExtractedData.total_amount <= amount_max)
    
    # Confidence filter
    confidence_min = filters.get("confidence_min")
    if confidence_min is not None:
        query = query.where(ExtractedData.extraction_confidence >= confidence_min)
    
    # Validation status filter
    validation_status = filters.get("validation_status")
    if validation_status:
        from sqlalchemy import func, select
        from core.models import ValidationResult, ValidationStatus
        
        # Filter by validation status
        if validation_status == "all_passed":
            # All validations passed - use subquery
            subquery = (
                select(ValidationResult.invoice_id)
                .where(ValidationResult.status == ValidationStatus.FAILED)
                .distinct()
            )
            query = query.where(~Invoice.id.in_(subquery))
        elif validation_status == "has_failed":
            # Has at least one failed validation
            subquery = (
                select(ValidationResult.invoice_id)
                .where(ValidationResult.status == ValidationStatus.FAILED)
                .distinct()
            )
            query = query.where(Invoice.id.in_(subquery))
        elif validation_status == "has_warning":
            # Has at least one warning
            subquery = (
                select(ValidationResult.invoice_id)
                .where(ValidationResult.status == ValidationStatus.WARNING)
                .distinct()
            )
            query = query.where(Invoice.id.in_(subquery))
    
    return query

