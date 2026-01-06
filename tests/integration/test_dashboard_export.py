"""Integration tests for dashboard export functionality."""

from datetime import date, datetime
from decimal import Decimal

import pytest

from interface.dashboard.components.export_utils import (
    export_invoice_detail_to_pdf,
    export_invoice_list_to_csv,
)


@pytest.fixture
def sample_invoices():
    """Sample invoice data for testing."""
    return [
        {
            "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
            "file_name": "invoice-1.png",
            "processing_status": "completed",
            "vendor_name": "Test Vendor A",
            "total_amount": Decimal("1000.00"),
            "currency": "USD",
            "invoice_date": date(2024, 1, 15),
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
        },
        {
            "invoice_id": "223e4567-e89b-12d3-a456-426614174001",
            "file_name": "invoice-2.png",
            "processing_status": "failed",
            "vendor_name": "Test Vendor B",
            "total_amount": None,
            "currency": None,
            "invoice_date": None,
            "created_at": datetime(2024, 1, 16, 11, 0, 0),
        },
    ]


@pytest.fixture
def sample_invoice_detail():
    """Sample invoice detail data for testing."""
    return {
        "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
        "file_name": "invoice-1.png",
        "file_type": "png",
        "processing_status": "completed",
        "created_at": datetime(2024, 1, 15, 10, 30, 0),
        "extracted_data": {
            "vendor_name": "Test Vendor A",
            "invoice_number": "INV-001",
            "invoice_date": date(2024, 1, 15),
            "total_amount": Decimal("1000.00"),
            "subtotal": Decimal("900.00"),
            "tax_amount": Decimal("100.00"),
            "currency": "USD",
        },
        "validation_results": [
            {
                "rule_name": "math_check_subtotal_tax",
                "status": "passed",
                "error_message": None,
            },
            {
                "rule_name": "vendor_sanity",
                "status": "passed",
                "error_message": None,
            },
        ],
    }


def test_csv_export_with_filtered_invoices(sample_invoices):
    """Test CSV export with filtered invoice list."""
    # Filter to only completed invoices
    filtered = [inv for inv in sample_invoices if inv["processing_status"] == "completed"]
    
    csv_bytes = export_invoice_list_to_csv(filtered)
    
    assert csv_bytes is not None
    csv_str = csv_bytes.decode("utf-8")
    
    # Should contain the completed invoice
    assert "invoice-1.png" in csv_str
    assert "Test Vendor A" in csv_str
    
    # Should not contain the failed invoice
    assert "invoice-2.png" not in csv_str or filtered == sample_invoices


def test_csv_export_with_all_invoices(sample_invoices):
    """Test CSV export with all invoices (no filtering)."""
    csv_bytes = export_invoice_list_to_csv(sample_invoices)
    
    assert csv_bytes is not None
    csv_str = csv_bytes.decode("utf-8")
    
    # Should contain both invoices
    assert "invoice-1.png" in csv_str
    assert "invoice-2.png" in csv_str


def test_pdf_export_with_invoice_detail(sample_invoice_detail):
    """Test PDF export with complete invoice detail."""
    pdf_bytes = export_invoice_detail_to_pdf(sample_invoice_detail)
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
    
    # Verify PDF contains expected content (basic check)
    pdf_str = pdf_bytes.decode("latin-1", errors="ignore")
    assert "Invoice Detail Report" in pdf_str or "invoice" in pdf_str.lower()


def test_pdf_export_with_minimal_detail():
    """Test PDF export with minimal invoice detail."""
    minimal_detail = {
        "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
        "file_name": "invoice-1.png",
        "processing_status": "processing",
        "created_at": datetime(2024, 1, 15, 10, 30, 0),
        "extracted_data": None,
        "validation_results": [],
    }
    
    pdf_bytes = export_invoice_detail_to_pdf(minimal_detail)
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")

