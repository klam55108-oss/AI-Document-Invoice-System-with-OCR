"""Unit tests for export utilities."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from interface.dashboard.components.export_utils import (
    export_invoice_detail_to_pdf,
    export_invoice_list_to_csv,
)


def test_export_invoice_list_to_csv_with_data():
    """Test CSV export with valid invoice data."""
    invoices = [
        {
            "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
            "file_name": "invoice-1.png",
            "processing_status": "completed",
            "vendor_name": "Test Vendor",
            "total_amount": Decimal("1000.00"),
            "currency": "USD",
            "invoice_date": date(2024, 1, 15),
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
        },
        {
            "invoice_id": "223e4567-e89b-12d3-a456-426614174001",
            "file_name": "invoice-2.png",
            "processing_status": "processing",
            "vendor_name": "Another Vendor",
            "total_amount": Decimal("2000.00"),
            "currency": "EUR",
            "invoice_date": date(2024, 1, 16),
            "created_at": datetime(2024, 1, 16, 11, 0, 0),
        },
    ]
    
    csv_bytes = export_invoice_list_to_csv(invoices)
    
    assert csv_bytes is not None
    assert len(csv_bytes) > 0
    csv_str = csv_bytes.decode("utf-8")
    assert "Invoice ID" in csv_str
    assert "File Name" in csv_str
    assert "invoice-1.png" in csv_str
    assert "invoice-2.png" in csv_str
    assert "Test Vendor" in csv_str


def test_export_invoice_list_to_csv_empty():
    """Test CSV export with empty invoice list."""
    invoices = []
    
    csv_bytes = export_invoice_list_to_csv(invoices)
    
    assert csv_bytes is not None
    csv_str = csv_bytes.decode("utf-8")
    assert "Invoice ID" in csv_str  # Should have headers even if empty


def test_export_invoice_list_to_csv_with_missing_fields():
    """Test CSV export with invoices missing some fields."""
    invoices = [
        {
            "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
            "file_name": "invoice-1.png",
            "processing_status": "completed",
            "vendor_name": None,
            "total_amount": None,
            "currency": None,
            "invoice_date": None,
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
        },
    ]
    
    csv_bytes = export_invoice_list_to_csv(invoices)
    
    assert csv_bytes is not None
    csv_str = csv_bytes.decode("utf-8")
    assert "invoice-1.png" in csv_str


def test_export_invoice_list_to_csv_to_file():
    """Test CSV export to file path."""
    invoices = [
        {
            "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
            "file_name": "invoice-1.png",
            "processing_status": "completed",
            "vendor_name": "Test Vendor",
            "total_amount": Decimal("1000.00"),
            "currency": "USD",
            "invoice_date": date(2024, 1, 15),
            "created_at": datetime(2024, 1, 15, 10, 30, 0),
        },
    ]
    
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_export.csv"
        csv_bytes = export_invoice_list_to_csv(invoices, output_path=output_path)
        
        assert output_path.exists()
        assert csv_bytes is not None
        assert len(csv_bytes) > 0


def test_export_invoice_detail_to_pdf():
    """Test PDF export with valid invoice detail."""
    invoice_detail = {
        "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
        "file_name": "invoice-1.png",
        "processing_status": "completed",
        "created_at": datetime(2024, 1, 15, 10, 30, 0),
        "extracted_data": {
            "vendor_name": "Test Vendor",
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
                "status": "failed",
                "error_message": "Vendor name is missing",
            },
        ],
    }
    
    pdf_bytes = export_invoice_detail_to_pdf(invoice_detail)
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    # PDF files start with %PDF
    assert pdf_bytes.startswith(b"%PDF")


def test_export_invoice_detail_to_pdf_minimal():
    """Test PDF export with minimal invoice detail."""
    invoice_detail = {
        "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
        "file_name": "invoice-1.png",
        "processing_status": "completed",
        "created_at": datetime(2024, 1, 15, 10, 30, 0),
        "extracted_data": None,
        "validation_results": [],
    }
    
    pdf_bytes = export_invoice_detail_to_pdf(invoice_detail)
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")


def test_export_invoice_detail_to_pdf_to_file():
    """Test PDF export to file path."""
    invoice_detail = {
        "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
        "file_name": "invoice-1.png",
        "processing_status": "completed",
        "created_at": datetime(2024, 1, 15, 10, 30, 0),
        "extracted_data": {
            "vendor_name": "Test Vendor",
            "invoice_number": "INV-001",
        },
        "validation_results": [],
    }
    
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_export.pdf"
        pdf_bytes = export_invoice_detail_to_pdf(invoice_detail, output_path=output_path)
        
        assert output_path.exists()
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

