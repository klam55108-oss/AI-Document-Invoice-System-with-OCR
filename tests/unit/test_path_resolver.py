"""Unit tests for file path resolution utility."""

import tempfile
from pathlib import Path

import pytest

from interface.dashboard.utils.path_resolver import ResolvedFileInfo, resolve_file_path


def test_resolve_file_path_found_in_original_location(tmp_path: Path) -> None:
    """Test resolving file path when file exists in original location."""
    # Create test data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    test_file = data_dir / "invoice-1.png"
    test_file.write_text("test content")

    result = resolve_file_path("invoice-1.png", data_dir=data_dir)

    assert result["exists"] is True
    assert result["location"] == "original"
    assert result["resolved_path"] == test_file
    assert result["error"] is None
    assert result["original_path"] == "invoice-1.png"


def test_resolve_file_path_found_in_encrypted_location(tmp_path: Path) -> None:
    """Test resolving file path when file exists in encrypted location."""
    # Create test data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    encrypted_dir = data_dir / "encrypted"
    encrypted_dir.mkdir()
    file_hash = "a" * 64
    encrypted_file = encrypted_dir / f"{file_hash}.encrypted"
    encrypted_file.write_text("encrypted content")

    result = resolve_file_path("invoice-1.png", file_hash=file_hash, data_dir=data_dir)

    assert result["exists"] is True
    assert result["location"] == "encrypted"
    assert result["resolved_path"] == encrypted_file
    assert result["error"] is None
    assert result["original_path"] == "invoice-1.png"


def test_resolve_file_path_not_found(tmp_path: Path) -> None:
    """Test resolving file path when file doesn't exist."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    result = resolve_file_path("nonexistent.png", data_dir=data_dir)

    assert result["exists"] is False
    assert result["location"] is None
    assert result["resolved_path"] is None
    assert result["error"] is not None
    assert "not found" in result["error"].lower()


def test_resolve_file_path_no_path_provided() -> None:
    """Test resolving file path when no path is provided."""
    result = resolve_file_path(None)

    assert result["exists"] is False
    assert result["location"] is None
    assert result["resolved_path"] is None
    assert result["error"] == "No file path provided"
    assert result["original_path"] == ""


def test_resolve_file_path_encrypted_fallback(tmp_path: Path) -> None:
    """Test that encrypted location is checked when original not found."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    encrypted_dir = data_dir / "encrypted"
    encrypted_dir.mkdir()
    file_hash = "b" * 64
    encrypted_file = encrypted_dir / f"{file_hash}.encrypted"
    encrypted_file.write_text("encrypted")

    # File doesn't exist in original location
    result = resolve_file_path("missing.png", file_hash=file_hash, data_dir=data_dir)

    assert result["exists"] is True
    assert result["location"] == "encrypted"
    assert result["resolved_path"] == encrypted_file


def test_resolve_file_path_neither_location_exists(tmp_path: Path) -> None:
    """Test when file doesn't exist in either location."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    result = resolve_file_path("missing.png", file_hash="c" * 64, data_dir=data_dir)

    assert result["exists"] is False
    assert result["location"] is None
    assert result["error"] is not None
    assert "not found" in result["error"].lower()

