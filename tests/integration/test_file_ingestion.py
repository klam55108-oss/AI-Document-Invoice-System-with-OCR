"""Integration tests for file ingestion pipeline."""

import tempfile
from pathlib import Path

import pytest

from ingestion.file_discovery import discover_files, get_file_type, is_supported_file
from ingestion.file_hasher import calculate_file_hash


@pytest.mark.asyncio
async def test_file_discovery():
    """Test file discovery in data directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # Create test files
        (data_dir / "invoice1.pdf").write_text("test")
        (data_dir / "invoice2.xlsx").write_text("test")
        (data_dir / "readme.txt").write_text("test")  # Not supported

        files = []
        async for file_path in discover_files(data_dir):
            files.append(file_path)

        # Should find 2 files (PDF and Excel), not the .txt
        assert len(files) == 2
        assert any(f.suffix == ".pdf" for f in files)
        assert any(f.suffix == ".xlsx" for f in files)


def test_get_file_type():
    """Test file type detection."""
    assert get_file_type(Path("test.pdf")) == "pdf"
    assert get_file_type(Path("test.xlsx")) == "xlsx"
    assert get_file_type(Path("test.csv")) == "csv"
    assert get_file_type(Path("test.jpg")) == "jpg"
    assert get_file_type(Path("test.jpeg")) == "jpg"  # Normalized
    assert get_file_type(Path("test.xls")) == "xlsx"  # Normalized


def test_is_supported_file():
    """Test supported file check."""
    assert is_supported_file(Path("test.pdf")) is True
    assert is_supported_file(Path("test.xlsx")) is True
    assert is_supported_file(Path("test.txt")) is False
    assert is_supported_file(Path("test.doc")) is False


def test_file_hash_integration():
    """Test file hashing as part of ingestion."""
    with tempfile.NamedTemporaryFile(delete=False, mode="wb", suffix=".pdf") as f:
        test_content = b"sample invoice content for testing"
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        # Calculate hash
        hash_value = calculate_file_hash(temp_path)

        # Verify hash format
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value.lower())

        # Verify file type
        assert is_supported_file(temp_path) is True
        assert get_file_type(temp_path) == "pdf"

    finally:
        temp_path.unlink()

