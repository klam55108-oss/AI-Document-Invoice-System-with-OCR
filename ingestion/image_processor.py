"""Image processing using PaddleOCR for text extraction."""

from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)

# Initialize PaddleOCR (CPU mode by default for compatibility)
# This will download the models on first use
_ocr_engine = None


def get_ocr_engine(lang: str = "ch"):
    """Lazy initialization of the OCR engine.
    
    Args:
        lang: Language code for OCR. Default "ch" (Chinese) supports both Chinese and English.
              Use "en" for English-only, "ch" for Chinese (which also handles English).
    """
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR engine", lang=lang)
            # Use "ch" (Chinese) as default - it supports both Chinese and English text
            # This is better for international invoices
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        except ImportError:
            logger.error("PaddleOCR not installed. Please install paddleocr and paddlepaddle.")
            raise
    return _ocr_engine


async def process_image(file_path: Path) -> dict[str, Any]:
    """Process image file using PaddleOCR to extract text.

    Args:
        file_path: Path to image file

    Returns:
        Dictionary with extracted text and metadata
    """
    logger.info("Starting OCR processing", path=str(file_path))

    try:
        ocr = get_ocr_engine()
        # PaddleOCR expects string path or numpy array
        result = ocr.ocr(str(file_path), cls=True)

        if not result or not result[0]:
            logger.warning("OCR returned no results", path=str(file_path))
            return {
                "text": "",
                "metadata": {
                    "file_path": str(file_path),
                    "processor": "paddleocr",
                    "status": "no_text_found",
                },
            }

        # Extract text from result
        # result structure: [ [[ [coords], (text, confidence) ], ...] ]
        extracted_text = []
        confidences = []

        for line in result[0]:
            text, confidence = line[1]
            extracted_text.append(text)
            confidences.append(float(confidence))

        full_text = "\n".join(extracted_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(
            "OCR processing completed",
            path=str(file_path),
            text_length=len(full_text),
            confidence=avg_confidence,
        )

        return {
            "text": full_text,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "paddleocr",
                "avg_confidence": avg_confidence,
                "line_count": len(extracted_text),
            },
        }

    except Exception as e:
        logger.error("OCR processing failed", path=str(file_path), error=str(e))
        # Fallback to empty result but mark as failed
        return {
            "text": "",
            "metadata": {
                "file_path": str(file_path),
                "processor": "paddleocr",
                "status": "error",
                "error": str(e),
            },
        }

