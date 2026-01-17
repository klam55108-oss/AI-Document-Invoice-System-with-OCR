"""Contract tests for OCR provider endpoints."""
import pytest

from interface.api.routes import ocr as ocr_routes


@pytest.mark.asyncio
async def test_list_ocr_providers_contract(client_with_db, monkeypatch) -> None:
    """List OCR providers returns expected envelope."""
    monkeypatch.setattr(ocr_routes, "provider_status", lambda _: "available")

    response = await client_with_db.get("/api/v1/ocr/providers")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert isinstance(payload["data"], list)
