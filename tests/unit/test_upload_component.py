"""Unit tests for upload component."""

import pytest

from interface.dashboard.components.upload import ACCEPTED_TYPES, MAX_FILE_SIZE


def test_accepted_file_types():
    """Test that accepted file types match supported formats."""
    expected_types = [".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png", ".webp", ".avif"]
    assert set(ACCEPTED_TYPES) == set(expected_types)


def test_max_file_size_limit():
    """Test that maximum file size is set to 50MB."""
    assert MAX_FILE_SIZE == 50 * 1024 * 1024  # 50MB in bytes


def test_file_type_validation():
    """Test file type validation logic."""
    from pathlib import Path
    from ingestion.file_discovery import is_supported_file
    
    # Test supported types
    assert is_supported_file(Path("test.pdf"))
    assert is_supported_file(Path("test.xlsx"))
    assert is_supported_file(Path("test.csv"))
    assert is_supported_file(Path("test.jpg"))
    assert is_supported_file(Path("test.png"))
    
    # Test unsupported types
    assert not is_supported_file(Path("test.txt"))
    assert not is_supported_file(Path("test.doc"))
    assert not is_supported_file(Path("test.exe"))


def test_file_size_validation():
    """Test file size validation logic."""
    # File size should be checked against MAX_FILE_SIZE
    assert MAX_FILE_SIZE == 52428800  # 50MB


def test_filename_sanitization():
    """Test filename sanitization prevents path traversal."""
    from interface.api.routes.uploads import sanitize_filename
    
    # Test path traversal attempts
    assert ".." not in sanitize_filename("../../../etc/passwd")
    assert "/" not in sanitize_filename("../../file.pdf")
    assert "\\" not in sanitize_filename("..\\..\\file.pdf")
    
    # Test normal filenames
    assert sanitize_filename("invoice-1.pdf") == "invoice-1.pdf"
    assert sanitize_filename("test file.xlsx") == "test file.xlsx"


def test_subfolder_validation():
    """Test subfolder name validation."""
    from interface.api.routes.uploads import validate_subfolder
    
    # Valid subfolders
    assert validate_subfolder("uploads")
    assert validate_subfolder("grok")
    assert validate_subfolder("jimeng")
    
    # Invalid subfolders (path traversal attempts)
    assert not validate_subfolder("../uploads")
    assert not validate_subfolder("uploads/../other")
    assert not validate_subfolder("")
    assert not validate_subfolder("   ")

