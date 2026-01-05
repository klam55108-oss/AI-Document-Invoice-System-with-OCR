"""Pydantic models for invoice data extraction and validation."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


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
    tax_rate: Decimal | None = Field(None, ge=0, le=1, description="Tax rate (0-1)")
    total_amount: Decimal | None = Field(None, ge=0, description="Total amount")
    currency: str | None = Field("USD", description="Currency code (ISO 4217)")
    line_items: list[LineItem] | None = Field(None, description="Line items")
    raw_text: str | None = Field(None, description="Full extracted text")
    extraction_confidence: Decimal | None = Field(
        None, ge=0, le=1, description="Extraction confidence (0-1)"
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        """Validate currency code."""
        if v is None:
            return None
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v.upper()

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

    class Config:
        json_schema_extra = {
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


class ValidationRuleResult(BaseModel):
    """Result of a validation rule check."""

    rule_name: str = Field(..., description="Validation rule identifier")
    rule_description: str | None = Field(None, description="Human-readable description")
    status: str = Field(..., description="Validation status: passed, failed, warning")
    expected_value: Decimal | None = Field(None, description="Expected calculated value")
    actual_value: Decimal | None = Field(None, description="Actual value from invoice")
    tolerance: Decimal | None = Field(None, description="Allowed tolerance")
    error_message: str | None = Field(None, description="Error details if failed")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        if v not in {"passed", "failed", "warning"}:
            raise ValueError("Status must be one of: passed, failed, warning")
        return v

