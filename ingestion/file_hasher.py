"""SHA-256 hash calculation for file content."""

import hashlib
from pathlib import Path

from core.logging import get_logger

logger = get_logger(__name__)


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file content.

    Args:
        file_path: Path to file

    Returns:
        SHA-256 hash as hex string (64 characters)

    Raises:
        FileNotFoundError: If file does not exist
        IOError: If file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    file_size = file_path.stat().st_size

    logger.debug("Calculating hash", path=str(file_path), size=file_size)

    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)

        hash_value = sha256_hash.hexdigest()
        logger.debug("Hash calculated", path=str(file_path), hash=hash_value[:8] + "...")
        return hash_value

    except IOError as e:
        logger.error("Failed to read file for hashing", path=str(file_path), error=str(e))
        raise


def validate_hash_format(hash_value: str) -> bool:
    """Validate SHA-256 hash format.

    Args:
        hash_value: Hash string to validate

    Returns:
        True if hash is valid SHA-256 format (64 hex characters)
    """
    if len(hash_value) != 64:
        return False

    try:
        int(hash_value, 16)
        return True
    except ValueError:
        return False

