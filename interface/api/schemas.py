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
    category: str | None = Field(None, description="Logical category (e.g. Invoice, Receipt)")
    group: str | None = Field(None, description="Logical group/source (e.g. grok, jimeng)")
    job_id: str | None = Field(None, description="Batch/Job identifier (UUID)")
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
    storage_path: str | None = Field(None, description="Storage path or key")
    category: str | None = Field(None, description="Category")
    group: str | None = Field(None, description="Group")
    job_id: str | None = Field(None, description="Job ID")
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


# Upload schemas (defined before InvoiceDetail to avoid forward reference)
class UploadMetadata(BaseModel):
    """Upload metadata structure."""

    subfolder: str = Field(..., description="Subfolder within data/ directory")
    group: str | None = Field(None, description="Group/batch identifier")
    category: str | None = Field(None, description="Category for organizing uploads")
    upload_source: str = Field(..., description="Source of upload", examples=["web-ui", "data-folder"])
    uploaded_at: datetime | None = Field(None, description="Upload timestamp")


class InvoiceDetail(BaseModel):
    """Detailed invoice information."""

    id: str
    file_name: str
    storage_path: str
    category: str | None = None
    group: str | None = None
    job_id: str | None = None
    file_type: str
    file_hash: str
    version: int
    processing_status: str
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None = None
    error_message: str | None = None
    upload_metadata: UploadMetadata | None = None
    extracted_data: ExtractedDataResponse | None = None
    validation_results: list[ValidationResultResponse] = Field(default_factory=list)


class InvoiceDetailResponse(ApiResponse):
    """Response for invoice detail endpoint."""

    data: InvoiceDetail


# Bulk operation schemas
class BulkReprocessRequest(BaseModel):
    """Request to reprocess multiple invoices."""

    invoice_ids: list[str] = Field(..., description="List of invoice UUIDs to reprocess", min_items=1)
    force_reprocess: bool = Field(False, description="Force reprocessing even if already processed")


class BulkActionItem(BaseModel):
    """Result for a single item in bulk action."""

    invoice_id: str = Field(..., description="Invoice UUID")
    status: str = Field(..., description="Action status", examples=["success", "failed", "skipped"])
    message: str | None = Field(None, description="Status message or error")


class BulkActionResponse(ApiResponse):
    """Response for bulk action endpoint."""

    total_requested: int = Field(..., description="Total number of invoices requested")
    successful: int = Field(..., description="Number of successful actions")
    failed: int = Field(..., description="Number of failed actions")
    skipped: int = Field(..., description="Number of skipped actions")
    results: list[BulkActionItem] = Field(..., description="Detailed results for each invoice")


class ProcessInvoiceData(BaseModel):
    """Data in process invoice response."""

    invoice_id: str
    job_id: str
    status: str


class ProcessInvoiceResponse(ApiResponse):
    """Response for process invoice endpoint."""

    data: ProcessInvoiceData


class UploadItem(BaseModel):
    """Individual file upload result."""

    file_name: str = Field(..., description="Original filename")
    invoice_id: str | None = Field(None, description="Invoice ID if processing started")
    status: str = Field(..., description="Current status", examples=["uploaded", "processing", "completed", "failed", "duplicate"])
    file_path: str | None = Field(None, description="Relative path from data/ directory")
    file_size: int | None = Field(None, description="File size in bytes")
    error_message: str | None = Field(None, description="Error message if upload failed")


class UploadData(BaseModel):
    """Data in upload response."""

    uploads: list[UploadItem] = Field(..., description="List of upload results")
    total: int = Field(..., description="Total number of files uploaded")
    successful: int = Field(..., description="Number of successfully uploaded files")
    failed: int = Field(..., description="Number of failed uploads")
    skipped: int = Field(..., description="Number of skipped files (duplicates)")


class UploadResponse(ApiResponse):
    """Response for upload endpoint."""

    data: UploadData


class UploadStatusData(BaseModel):
    """Data in upload status response."""

    invoice_id: str = Field(..., description="Invoice UUID")
    file_name: str = Field(..., description="Original filename")
    storage_path: str | None = Field(None, description="Relative path from data/ directory")
    category: str | None = Field(None, description="Category")
    group: str | None = Field(None, description="Group")
    job_id: str | None = Field(None, description="Job ID")
    processing_status: str = Field(..., description="Processing status")
    upload_metadata: UploadMetadata | None = Field(None, description="Upload metadata")
    error_message: str | None = Field(None, description="Error message if processing failed")


class UploadStatusResponse(ApiResponse):
    """Response for upload status endpoint."""

    data: UploadStatusData


# Chatbot schemas
class ChatRequest(BaseModel):
    """Request to send a chat message."""

    message: str = Field(..., description="User's natural language question or message")
    session_id: str = Field(..., description="Conversation session ID")
    language: str = Field("en", description="Preferred language for response (en/zh)", pattern="^(en|zh)$")


class ChatMessage(BaseModel):
    """Chat message in conversation."""

    message_id: str = Field(..., description="Unique message identifier")
    role: str = Field(..., description="Message role (user/assistant)", pattern="^(user|assistant)$")
    content: str = Field(..., description="Message text content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: dict[str, Any] | None = Field(None, description="Additional message metadata")


class ChatResponse(BaseModel):
    """Response for chat endpoint."""

    message: str = Field(..., description="Chatbot's response message")
    session_id: str = Field(..., description="Conversation session ID")
    invoice_ids: list[str] = Field(default_factory=list, description="Invoice IDs referenced in response")
    invoice_count: int = Field(0, description="Number of invoices in result set")
    has_more: bool = Field(False, description="Whether more results exist beyond limit")
    metadata: dict[str, Any] | None = Field(None, description="Additional response metadata")


class SessionResponse(BaseModel):
    """Response for session creation."""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")


class SessionDetailResponse(BaseModel):
    """Response for session detail endpoint."""

    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    messages: list[ChatMessage] = Field(..., description="Conversation message history (last 10 messages)")

