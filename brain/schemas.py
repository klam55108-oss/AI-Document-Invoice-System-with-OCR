"""Pydantic models for invoice data extraction and validation."""

from datetime import date, datetime, UTC
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LineItem(BaseModel):
    """Line item in an invoice."""

    description: str | None = Field(None, description="Item description")
    quantity: float | None = Field(None, ge=0, description="Quantity")
    unit_price: Decimal | None = Field(None, ge=0, description="Unit price")
    amount: Decimal | None = Field(None, ge=0, description="Line item amount")


class ExtractedDataSchema(BaseModel):
    """Schema for extracted invoice data."""

    vendor_name: str | None = Field(None, description="Vendor/supplier name")
    invoice_number: str | None = Field(None, description="Invoice number")
    invoice_date: date | None = Field(None, description="Invoice date")
    due_date: date | None = Field(None, description="Payment due date")
    subtotal: Decimal | None = Field(None, ge=0, description="Subtotal amount")
    tax_amount: Decimal | None = Field(None, ge=0, description="Tax amount")
    tax_rate: Decimal | None = Field(None, ge=0, description="Tax rate (e.g., 0.05 or 5.0)")
    total_amount: Decimal | None = Field(None, ge=0, description="Total amount")
    currency: str | None = Field("USD", description="Currency code (ISO 4217)")
    line_items: list[LineItem] | None = Field(None, description="Line items")
    raw_text: str | None = Field(None, description="Full extracted text")
    extraction_confidence: Decimal | None = Field(
        None, ge=0, le=1, description="Extraction confidence (0-1)"
    )
    
    # Per-field confidence scores (added for UI quality improvements)
    vendor_name_confidence: Decimal | None = Field(None, ge=0, le=1, description="Vendor name confidence (0-1)")
    invoice_number_confidence: Decimal | None = Field(None, ge=0, le=1, description="Invoice number confidence (0-1)")
    invoice_date_confidence: Decimal | None = Field(None, ge=0, le=1, description="Invoice date confidence (0-1)")
    total_amount_confidence: Decimal | None = Field(None, ge=0, le=1, description="Total amount confidence (0-1)")
    subtotal_confidence: Decimal | None = Field(None, ge=0, le=1, description="Subtotal confidence (0-1)")
    tax_amount_confidence: Decimal | None = Field(None, ge=0, le=1, description="Tax amount confidence (0-1)")
    currency_confidence: Decimal | None = Field(None, ge=0, le=1, description="Currency confidence (0-1)")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency code."""
        if v is None:
            return None
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v.upper()

    @field_validator("tax_rate")
    @classmethod
    def validate_tax_rate(cls, v: Decimal | None) -> Decimal | None:
        """Normalize tax rate (e.g., convert 5.0 to 0.05)."""
        if v is None:
            return None
        # If rate is > 1.0, assume it's a percentage and convert to decimal
        if v > 1:
            return v / 100
        return v

    @model_validator(mode="after")
    def validate_amounts(self) -> "ExtractedDataSchema":
        """Validate that subtotal + tax = total_amount."""
        if self.subtotal is not None and self.tax_amount is not None and self.total_amount is not None:
            expected_total = self.subtotal + self.tax_amount
            if abs(expected_total - self.total_amount) > Decimal("0.01"):
                # We don't raise here to allow the validator.py to capture it as a ValidationRuleResult
                # but we could log or mark it for self-correction refined logic.
                pass
        return self

    @model_validator(mode="after")
    def validate_dates(self) -> "ExtractedDataSchema":
        """Validate that due_date is after or equal to invoice_date."""
        if self.invoice_date and self.due_date:
            if self.due_date < self.invoice_date:
                # Same logic: don't raise, just let it be handled by rules framework
                pass
        return self
    
    @model_validator(mode="after")
    def calculate_overall_confidence(self) -> "ExtractedDataSchema":
        """Calculate overall extraction confidence from per-field scores."""
        if self.extraction_confidence is None:
            # Use critical fields for overall confidence calculation
            confidences = [
                self.vendor_name_confidence,
                self.invoice_number_confidence,
                self.total_amount_confidence,
            ]
            non_null_confidences = [c for c in confidences if c is not None]
            if non_null_confidences:
                self.extraction_confidence = sum(non_null_confidences) / Decimal(len(non_null_confidences))
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vendor_name": "Acme Corporation",
                "invoice_number": "INV-2024-001",
                "invoice_date": "2024-12-19",
                "subtotal": 1000.00,
                "tax_amount": 100.00,
                "total_amount": 1100.00,
                "currency": "USD",
            }
        }
    )


class ValidationRuleResult(BaseModel):
    """Result of a validation rule check."""

    rule_name: str = Field(..., description="Validation rule identifier")
    rule_description: str | None = Field(None, description="Human-readable description")
    status: str = Field(..., description="Validation status: passed, failed, warning")
    expected_value: Decimal | None = Field(None, description="Expected calculated value")
    actual_value: Decimal | None = Field(None, description="Actual value from invoice")
    tolerance: Decimal | None = Field(None, description="Allowed tolerance")
    error_message: str | None = Field(None, description="Error details if failed")
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Validation timestamp")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        if v not in {"passed", "failed", "warning"}:
            raise ValueError("Status must be one of: passed, failed, warning")
        return v

