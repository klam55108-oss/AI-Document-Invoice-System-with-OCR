"""Async file discovery in data directory."""

import os
from pathlib import Path
from typing import AsyncGenerator

from core.logging import get_logger

logger = get_logger(__name__)

# Supported file types
SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".jpg", ".jpeg", ".png"}


async def discover_files(data_dir: Path) -> AsyncGenerator[Path, None]:
    """Discover invoice files in the data directory.

    Args:
        data_dir: Path to data directory

    Yields:
        Path to each discovered file
    """
    if not data_dir.exists():
        logger.warning("Data directory does not exist", path=str(data_dir))
        return

    if not data_dir.is_dir():
        logger.error("Data path is not a directory", path=str(data_dir))
        return

    logger.info("Discovering files", directory=str(data_dir))

    for file_path in data_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            logger.debug("Found file", path=str(file_path), extension=file_path.suffix)
            yield file_path


def get_file_type(file_path: Path) -> str:
    """Get file type from extension.

    Args:
        file_path: Path to file

    Returns:
        File type string (pdf, xlsx, csv, jpg, png)
    """
    ext = file_path.suffix.lower()
    # Normalize extensions
    if ext == ".jpeg":
        return "jpg"
    if ext == ".xls":
        return "xlsx"  # Treat .xls as Excel format
    return ext.lstrip(".")


def is_supported_file(file_path: Path) -> bool:
    """Check if file is supported.

    Args:
        file_path: Path to file

    Returns:
        True if file is supported
    """
    return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

