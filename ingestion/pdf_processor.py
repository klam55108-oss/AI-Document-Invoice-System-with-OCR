"""PDF processing via Docling."""

from pathlib import Path
from typing import Any

from core.logging import get_logger

logger = get_logger(__name__)

# Docling will be imported when available
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logger.warning("Docling not available, PDF processing will be limited")


async def process_pdf(file_path: Path) -> dict[str, Any]:
    """Process PDF file and extract text.

    Args:
        file_path: Path to PDF file

    Returns:
        Dictionary with extracted text and metadata:
        - text: Extracted text content
        - pages: Number of pages (if available)
        - metadata: File metadata
    """
    if not DOCLING_AVAILABLE:
        logger.warning("Docling not available, using fallback PDF processing")
        return await _process_pdf_fallback(file_path)

    try:
        logger.info("Processing PDF with Docling", path=str(file_path))

        converter = DocumentConverter()
        result = converter.convert(str(file_path))

        # Extract text from result
        text_content = ""
        if hasattr(result, "document"):
            # Docling result structure
            if hasattr(result.document, "text"):
                text_content = result.document.text
            elif hasattr(result.document, "content"):
                # Try to extract text from content structure
                text_content = str(result.document.content)

        pages = getattr(result, "pages", None) or 1

        logger.info("PDF processed", path=str(file_path), pages=pages, text_length=len(text_content))

        return {
            "text": text_content,
            "pages": pages,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "docling",
            },
        }

    except Exception as e:
        logger.error("PDF processing failed with Docling, trying fallback", error=str(e))
        return await _process_pdf_fallback(file_path)


async def _process_pdf_fallback(file_path: Path) -> dict[str, Any]:
    """Fallback PDF processing using pypdf.

    Args:
        file_path: Path to PDF file

    Returns:
        Dictionary with extracted text
    """
    try:
        from pypdf import PdfReader

        logger.info("Processing PDF with pypdf fallback", path=str(file_path))

        reader = PdfReader(str(file_path))
        text_parts = []

        for page in reader.pages:
            text_parts.append(page.extract_text())

        text_content = "\n".join(text_parts)
        pages = len(reader.pages)

        logger.info("PDF processed with fallback", path=str(file_path), pages=pages)

        return {
            "text": text_content,
            "pages": pages,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "pypdf",
            },
        }

    except ImportError:
        logger.error("pypdf not available, cannot process PDF")
        raise RuntimeError("No PDF processing library available (docling or pypdf)")
    except Exception as e:
        logger.error("PDF fallback processing failed", error=str(e))
        raise

