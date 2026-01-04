"""Pydantic schemas for API request/response models."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Health status", examples=["healthy", "degraded"])
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    version: str = Field(..., description="API version", examples=["1.0.0"])

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-12-19T10:30:00Z",
                "version": "1.0.0",
            }
        }


# Request schemas
class ProcessInvoiceRequest(BaseModel):
    """Request to process an invoice file."""

    file_path: str = Field(..., description="Relative path to file in data/ directory")
    force_reprocess: bool = Field(False, description="Force reprocessing even if file hash exists")


# Response envelope schemas
class ApiResponse(BaseModel):
    """Base API response envelope."""

    status: str = Field(..., description="Response status", examples=["success", "error"])
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorDetail(BaseModel):
    """Error detail in error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class ErrorResponse(ApiResponse):
    """Error response envelope."""

    error: ErrorDetail


# Pagination schema
class Pagination(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


# Invoice schemas
class InvoiceSummary(BaseModel):
    """Summary of an invoice for list view."""

    id: str = Field(..., description="Invoice UUID")
    file_name: str = Field(..., description="Original filename")
    file_type: str | None = Field(None, description="File type")
    processing_status: str = Field(..., description="Processing status")
    vendor_name: str | None = Field(None, description="Vendor name")
    total_amount: float | None = Field(None, description="Total amount")
    currency: str | None = Field(None, description="Currency code")
    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: datetime | None = Field(None, description="Processing completion timestamp")


class InvoiceListResponse(ApiResponse):
    """Response for invoice list endpoint."""

    data: list[InvoiceSummary] = Field(..., description="List of invoices")
    pagination: Pagination = Field(..., description="Pagination metadata")


class LineItemResponse(BaseModel):
    """Line item in invoice."""

    description: str | None = None
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class ExtractedDataResponse(BaseModel):
    """Extracted invoice data."""

    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    subtotal: float | None = None
    tax_amount: float | None = None
    tax_rate: float | None = None
    total_amount: float | None = None
    currency: str | None = None
    line_items: list[LineItemResponse] | dict[str, Any] | None = None
    extraction_confidence: float | None = None


class ValidationResultResponse(BaseModel):
    """Validation result."""

    rule_name: str
    rule_description: str | None = None
    status: str
    expected_value: float | None = None
    actual_value: float | None = None
    error_message: str | None = None
    validated_at: datetime


class InvoiceDetail(BaseModel):
    """Detailed invoice information."""

    id: str
    file_name: str
    file_path: str
    file_type: str
    file_hash: str
    version: int
    processing_status: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None
    error_message: str | None = None
    extracted_data: ExtractedDataResponse | None = None
    validation_results: list[ValidationResultResponse] = Field(default_factory=list)


class InvoiceDetailResponse(ApiResponse):
    """Response for invoice detail endpoint."""

    data: InvoiceDetail


class ProcessInvoiceData(BaseModel):
    """Data in process invoice response."""

    invoice_id: str
    job_id: str
    status: str


class ProcessInvoiceResponse(ApiResponse):
    """Response for process invoice endpoint."""

    data: ProcessInvoiceData

