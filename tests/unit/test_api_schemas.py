"""Unit tests for API schemas."""

from datetime import date, datetime

import pytest

from interface.api.schemas import (
    ErrorResponse,
    InvoiceDetail,
    InvoiceListResponse,
    InvoiceSummary,
    Pagination,
    ProcessInvoiceRequest,
)


def test_process_invoice_request():
    """Test process invoice request schema."""
    request = ProcessInvoiceRequest(file_path="test.pdf", force_reprocess=False)
    assert request.file_path == "test.pdf"
    assert request.force_reprocess is False


def test_invoice_summary():
    """Test invoice summary schema."""
    summary = InvoiceSummary(
        id="123e4567-e89b-12d3-a456-426614174000",
        file_name="invoice.pdf",
        processing_status="completed",
        created_at=datetime.utcnow(),
    )
    assert summary.file_name == "invoice.pdf"
    assert summary.processing_status == "completed"


def test_pagination():
    """Test pagination schema."""
    pagination = Pagination(
        page=1,
        page_size=20,
        total_items=100,
        total_pages=5,
        has_next=True,
        has_previous=False,
    )
    assert pagination.page == 1
    assert pagination.total_pages == 5
    assert pagination.has_next is True


def test_invoice_list_response():
    """Test invoice list response schema."""
    response = InvoiceListResponse(
        status="success",
        data=[],
        pagination=Pagination(
            page=1,
            page_size=20,
            total_items=0,
            total_pages=0,
            has_next=False,
            has_previous=False,
        ),
    )
    assert response.status == "success"
    assert isinstance(response.data, list)
    assert response.pagination.total_items == 0


def test_invoice_detail():
    """Test invoice detail schema."""
    detail = InvoiceDetail(
        id="123e4567-e89b-12d3-a456-426614174000",
        file_name="invoice.pdf",
        file_path="data/invoice.pdf",
        file_type="pdf",
        file_hash="a" * 64,
        version=1,
        processing_status="completed",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    assert detail.file_name == "invoice.pdf"
    assert detail.version == 1


def test_error_response():
    """Test error response schema."""
    from interface.api.schemas import ErrorDetail

    error = ErrorResponse(
        status="error",
        error=ErrorDetail(code="NOT_FOUND", message="Resource not found"),
    )
    assert error.status == "error"
    assert error.error.code == "NOT_FOUND"

