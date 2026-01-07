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
        - text: Extracted text content (Markdown)
        - pages: Number of pages
        - tables: List of extracted tables as CSV/Markdown
        - metadata: File metadata
    """
    if not DOCLING_AVAILABLE:
        logger.warning("Docling not available, using fallback PDF processing")
        return await _process_pdf_fallback(file_path)

    try:
        logger.info("Processing PDF with Docling", path=str(file_path))

        converter = DocumentConverter()
        result = converter.convert(str(file_path))

        # Extract markdown content for layout preservation
        text_content = result.document.export_to_markdown()

        # Extract tables as structured data
        tables = []
        if hasattr(result.document, "tables"):
            for table in result.document.tables:
                try:
                    # Convert table to markdown for better LLM/parsing context
                    tables.append(table.export_to_markdown())
                except Exception:
                    logger.warning("Failed to export table to markdown")

        pages = getattr(result, "pages", None) or 1
        if not pages and hasattr(result.document, "pages"):
            pages = len(result.document.pages)

        logger.info(
            "PDF processed with Docling",
            path=str(file_path),
            pages=pages,
            text_length=len(text_content),
            tables_found=len(tables),
        )

        return {
            "text": text_content,
            "pages": pages,
            "tables": tables,
            "metadata": {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "processor": "docling",
                "format": "markdown",
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
        error_msg = "No PDF processing library available. Please install either 'docling' or 'pypdf'."
        logger.error("PDF processing failed - no library available", path=str(file_path), error=error_msg)
        raise RuntimeError(error_msg) from None
    except FileNotFoundError as e:
        error_msg = f"PDF file not found: {file_path}"
        logger.error("PDF processing failed - file not found", path=str(file_path), error=error_msg)
        raise FileNotFoundError(error_msg) from e
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"PDF processing failed: {str(e)}"
        logger.error(
            "PDF fallback processing failed",
            path=str(file_path),
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        raise RuntimeError(f"PDF processing failed ({error_type}): {str(e)}") from e

