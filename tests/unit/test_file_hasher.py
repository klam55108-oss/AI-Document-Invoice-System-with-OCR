"""Unit tests for file hasher."""

import tempfile
from pathlib import Path

import pytest

from ingestion.file_hasher import calculate_file_hash, validate_hash_format


def test_calculate_file_hash():
    """Test hash calculation for a file."""
    with tempfile.NamedTemporaryFile(delete=False, mode="wb") as f:
        test_content = b"test invoice content"
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        hash_value = calculate_file_hash(temp_path)
        assert len(hash_value) == 64
        assert validate_hash_format(hash_value)
        # Hash should be deterministic
        hash_value2 = calculate_file_hash(temp_path)
        assert hash_value == hash_value2
    finally:
        temp_path.unlink()


def test_validate_hash_format():
    """Test hash format validation."""
    assert validate_hash_format("a" * 64) is True
    assert validate_hash_format("0" * 64) is True
    assert validate_hash_format("A" * 64) is True  # Hex allows uppercase
    assert validate_hash_format("a" * 63) is False  # Too short
    assert validate_hash_format("a" * 65) is False  # Too long
    assert validate_hash_format("g" * 64) is False  # Invalid hex character
    assert validate_hash_format("") is False


def test_calculate_file_hash_nonexistent():
    """Test hash calculation for non-existent file."""
    with pytest.raises(FileNotFoundError):
        calculate_file_hash(Path("/nonexistent/file.pdf"))


def test_calculate_file_hash_directory():
    """Test hash calculation for directory (should fail)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            calculate_file_hash(Path(tmpdir))

