"""Integration tests for OCR provider admin configuration."""
import pytest

from interface.api.routes import ocr as ocr_routes


@pytest.mark.asyncio
async def test_update_ocr_providers_admin(client_with_db, monkeypatch) -> None:
    """Admin can update enabled and default providers."""
    monkeypatch.setattr(ocr_routes, "provider_status", lambda _: "available")

    headers = {"X-User-Role": "operator"}
    enabled_response = await client_with_db.patch(
        "/api/v1/ocr/providers/enabled",
        json={"provider_ids": ["paddleocr", "deepseek-ocr"]},
        headers=headers,
    )
    assert enabled_response.status_code == 200

    default_response = await client_with_db.patch(
        "/api/v1/ocr/providers/default",
        json={"provider_id": "paddleocr"},
        headers=headers,
    )
    assert default_response.status_code == 200
    payload = default_response.json()
    defaults = [item for item in payload["data"] if item["is_default"]]
    assert defaults[0]["provider_id"] == "paddleocr"
