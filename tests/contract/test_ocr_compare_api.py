"""Contract tests for OCR comparison endpoints."""
from pathlib import Path

import pytest

from core.ocr import configuration as ocr_config
from core.config import settings


@pytest.mark.asyncio
async def test_ocr_compare_contract(client_with_db, monkeypatch) -> None:
    """Compare OCR returns side-by-side results."""
    data_dir = Path("data").resolve()
    data_dir.mkdir(exist_ok=True)
    sample_path = data_dir / "test-ocr-compare.png"
    sample_path.write_bytes(b"fake")

    async def fake_process_image(file_path: Path, provider_id: str | None = None):
        return {"text": f"text-{provider_id}", "metadata": {"file_path": str(file_path)}}

    monkeypatch.setattr("core.ocr.service.process_image", fake_process_image)
    monkeypatch.setattr(ocr_config, "provider_status", lambda _: "available")
    monkeypatch.setattr(settings, "OCR_INCLUDE_KEY_FIELDS", False)

    response = await client_with_db.post(
        "/api/v1/ocr/compare",
        json={
            "input_id": "test-ocr-compare.png",
            "provider_a_id": "paddleocr",
            "provider_b_id": "deepseek-ocr",
        },
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "success"
    data = payload["data"]
    assert data["provider_a_result"]["provider_id"] == "paddleocr"
    assert data["provider_b_result"]["provider_id"] == "deepseek-ocr"
