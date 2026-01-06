"""Integration tests for upload API endpoints."""

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    """Create a sample PDF file for testing."""
    pdf_file = tmp_path / "test_invoice.pdf"
    # Create a minimal PDF file
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 0\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    pdf_file.write_bytes(pdf_content)
    return pdf_file


@pytest.fixture
def sample_image_file(tmp_path: Path) -> Path:
    """Create a sample image file for testing."""
    image_file = tmp_path / "test_invoice.png"
    # Create a minimal PNG file (PNG header)
    png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    image_file.write_bytes(png_content)
    return image_file


def test_upload_single_file(sample_pdf_file: Path):
    """Test uploading a single file."""
    with open(sample_pdf_file, "rb") as f:
        response = client.post(
            "/api/v1/uploads",
            files={"files": ("test_invoice.pdf", f, "application/pdf")},
            data={"subfolder": "uploads", "force_reprocess": "false"},
        )
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert len(data["data"]["uploads"]) == 1
    assert data["data"]["successful"] == 1


def test_upload_file_type_validation():
    """Test file type validation rejects unsupported types."""
    unsupported_file = ("test.txt", b"test content", "text/plain")
    response = client.post(
        "/api/v1/uploads",
        files={"files": unsupported_file},
        data={"subfolder": "uploads"},
    )
    
    assert response.status_code in [400, 422]
    # Should reject unsupported file type


def test_upload_file_size_validation(tmp_path: Path):
    """Test file size validation enforces 50MB limit."""
    # Create a file larger than 50MB
    large_file = tmp_path / "large_file.pdf"
    large_content = b"x" * (51 * 1024 * 1024)  # 51MB
    large_file.write_bytes(large_content)
    
    with open(large_file, "rb") as f:
        response = client.post(
            "/api/v1/uploads",
            files={"files": ("large_file.pdf", f, "application/pdf")},
            data={"subfolder": "uploads"},
        )
    
    # Should reject file that's too large
    assert response.status_code in [400, 413]


def test_upload_multiple_files(sample_pdf_file: Path, sample_image_file: Path):
    """Test uploading multiple files."""
    files = [
        ("files", ("test_invoice.pdf", open(sample_pdf_file, "rb"), "application/pdf")),
        ("files", ("test_invoice.png", open(sample_image_file, "rb"), "image/png")),
    ]
    
    response = client.post(
        "/api/v1/uploads",
        files=files,
        data={"subfolder": "uploads", "force_reprocess": "false"},
    )
    
    # Close file handles
    for _, (_, file_obj, _) in files:
        file_obj.close()
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]["uploads"]) == 2


def test_upload_status_endpoint():
    """Test getting upload status."""
    # First need to upload a file to get an invoice_id
    # This is a placeholder - actual test would upload first
    invoice_id = uuid.uuid4()
    response = client.get(f"/api/v1/uploads/{invoice_id}/status")
    
    # Should return 404 if invoice doesn't exist, or 200 with status if it does
    assert response.status_code in [200, 404]


def test_upload_duplicate_detection(sample_pdf_file: Path):
    """Test duplicate file detection."""
    # Upload file first time
    with open(sample_pdf_file, "rb") as f:
        response1 = client.post(
            "/api/v1/uploads",
            files={"files": ("test_invoice.pdf", f, "application/pdf")},
            data={"subfolder": "uploads", "force_reprocess": "false"},
        )
    
    assert response1.status_code == 202
    
    # Upload same file again
    with open(sample_pdf_file, "rb") as f:
        response2 = client.post(
            "/api/v1/uploads",
            files={"files": ("test_invoice.pdf", f, "application/pdf")},
            data={"subfolder": "uploads", "force_reprocess": "false"},
        )
    
    assert response2.status_code == 202
    data = response2.json()
    # Should detect duplicate
    assert data["data"]["skipped"] >= 1 or any(
        item["status"] == "duplicate" for item in data["data"]["uploads"]
    )

