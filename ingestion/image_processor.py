"""Image processing placeholder for future implementation."""

from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)


async def process_image(file_path: Path) -> dict[str, Any]:
    """Process image file (placeholder for future OCR implementation).

    Args:
        file_path: Path to image file

    Returns:
        Dictionary with placeholder data

    Note:
        This is a placeholder. Future implementation will use OCR
        (e.g., PaddleOCR, Tesseract) to extract text from images.
    """
    logger.warning("Image processing not yet implemented", path=str(file_path))

    return {
        "text": "",
        "metadata": {
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "processor": "placeholder",
            "note": "Image OCR not implemented in scaffold phase",
        },
    }

