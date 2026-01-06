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
            import os
            # Disable model source connectivity check to speed up initialization
            # This prevents the "Checking connectivity to the model hosters" delay
            os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
            
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR engine", lang=lang)
            # Use "ch" (Chinese) as default - it supports both Chinese and English text
            # This is better for international invoices
            # use_angle_cls is deprecated, use use_textline_orientation if available
            _ocr_engine = PaddleOCR(use_textline_orientation=True, lang=lang)
        except (ImportError, TypeError):
            try:
                # Fallback to older version args
                _ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang)
            except Exception:
                logger.error("PaddleOCR not installed or initialization failed.")
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
        # Some versions use predict(), older use ocr()
        if hasattr(ocr, "predict"):
            result = ocr.predict(str(file_path))
        else:
            result = ocr.ocr(str(file_path))

        if not result:
            logger.warning("OCR returned no results", path=str(file_path))
            return {
                "text": "",
                "metadata": {
                    "file_path": str(file_path),
                    "processor": "paddleocr",
                    "status": "no_text_found",
                },
            }

        extracted_text = []
        confidences = []

        # Handle different result structures
        res0 = result[0]
        
        # New OCRResult object from PaddleX/PaddleOCR newer versions
        # It often behaves like a dict or has these attributes
        if hasattr(res0, "rec_texts") and hasattr(res0, "rec_scores"):
            extracted_text = res0.rec_texts
            confidences = [float(c) for c in res0.rec_scores]
        elif isinstance(res0, dict) and "rec_texts" in res0 and "rec_scores" in res0:
            extracted_text = res0["rec_texts"]
            confidences = [float(c) for c in res0["rec_scores"]]
        # Legacy list-of-lists structure: [ [[ [coords], (text, confidence) ], ...] ]
        elif isinstance(res0, list):
            for line in res0:
                if len(line) > 1 and isinstance(line[1], (tuple, list)):
                    text, confidence = line[1]
                    extracted_text.append(text)
                    confidences.append(float(confidence))
        else:
            logger.warning("Unknown OCR result structure", type=str(type(res0)))

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

