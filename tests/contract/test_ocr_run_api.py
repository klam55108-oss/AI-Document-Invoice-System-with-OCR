"""Contract tests for OCR run endpoints."""
from pathlib import Path

import pytest

from core.ocr import configuration as ocr_config
from core.config import settings


@pytest.mark.asyncio
async def test_ocr_run_contract(client_with_db, monkeypatch) -> None:
    """Run OCR returns expected envelope."""
    data_dir = Path("data").resolve()
    data_dir.mkdir(exist_ok=True)
    sample_path = data_dir / "test-ocr.png"
    sample_path.write_bytes(b"fake")

    async def fake_process_image(file_path: Path, provider_id: str | None = None):
        return {"text": "sample text", "metadata": {"file_path": str(file_path)}}

    monkeypatch.setattr("core.ocr.service.process_image", fake_process_image)
    monkeypatch.setattr(ocr_config, "provider_status", lambda _: "available")
    monkeypatch.setattr(settings, "OCR_INCLUDE_KEY_FIELDS", False)

    response = await client_with_db.post(
        "/api/v1/ocr/run",
        json={"input_id": "test-ocr.png", "provider_id": "paddleocr"},
    )
    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["provider_id"] == "paddleocr"
    assert payload["data"]["extracted_text"] == "sample text"

    result_id = payload["data"]["result_id"]
    result_response = await client_with_db.get(f"/api/v1/ocr/results/{result_id}")
    assert result_response.status_code == 200
    result_payload = result_response.json()
    assert result_payload["data"]["result_id"] == result_id
    assert result_payload["data"]["provider_id"] == "paddleocr"
