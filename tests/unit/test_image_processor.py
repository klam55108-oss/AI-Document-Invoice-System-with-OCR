"""Unit tests for image processor."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.image_processor import process_image


@pytest.mark.asyncio
async def test_process_image_success():
    """Test successful OCR processing with mocked PaddleOCR."""
    mock_result = [
        [
            [[[0, 0], [10, 0], [10, 10], [0, 10]], ("INVOICE", 0.99)],
            [[[0, 20], [10, 20], [10, 30], [0, 30]], ("#12345", 0.95)],
        ]
    ]

    with patch("ingestion.image_processor.get_ocr_engine") as mock_get_engine:
        mock_instance = MagicMock()
        mock_instance.ocr.return_value = mock_result
        mock_get_engine.return_value = mock_instance

        file_path = Path("tests/fixtures/sample_invoice.jpg")
        # Ensure path exists for stat() call in process_image
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1024
            
            result = await process_image(file_path)

            assert result["text"] == "INVOICE\n#12345"
            assert result["metadata"]["processor"] == "paddleocr"
            assert result["metadata"]["avg_confidence"] == pytest.approx(0.97)
            assert result["metadata"]["line_count"] == 2


@pytest.mark.asyncio
async def test_process_image_no_results():
    """Test OCR processing with no results."""
    mock_result = [[]]

    with patch("ingestion.image_processor.get_ocr_engine") as mock_get_engine:
        mock_instance = MagicMock()
        mock_instance.ocr.return_value = mock_result
        mock_get_engine.return_value = mock_instance

        file_path = Path("tests/fixtures/empty.jpg")
        # Ensure path exists for stat() call in process_image
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 0
            result = await process_image(file_path)

            assert result["text"] == ""
            assert result["metadata"]["status"] == "no_text_found"


@pytest.mark.asyncio
async def test_process_image_error():
    """Test OCR processing with an error."""
    with patch("ingestion.image_processor.get_ocr_engine") as mock_get_engine:
        mock_instance = MagicMock()
        mock_instance.ocr.side_effect = Exception("OCR Error")
        mock_get_engine.return_value = mock_instance

        file_path = Path("tests/fixtures/error.jpg")
        result = await process_image(file_path)

        assert result["text"] == ""
        assert result["metadata"]["status"] == "error"
        assert "OCR Error" in result["metadata"]["error"]
