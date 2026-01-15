"""Contract tests for configuration detail and rollback APIs."""

from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_configuration_detail_contract() -> None:
    """Configuration detail endpoint returns expected envelope."""
    headers = {"X-User-Role": "operator"}
    payload = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v1"}]}

    create_response = client.post("/api/v1/configurations", json=payload, headers=headers)
    config_id = create_response.json()["data"]["config_id"]

    detail_response = client.get(f"/api/v1/configurations/{config_id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["status"] == "success"
    assert detail_body["data"]["config_id"] == config_id


def test_configuration_rollback_contract() -> None:
    """Rollback endpoint returns queued status."""
    headers = {"X-User-Role": "operator"}
    payload = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v1"}]}

    create_response = client.post("/api/v1/configurations", json=payload, headers=headers)
    config_id = create_response.json()["data"]["config_id"]

    rollback_response = client.post(
        f"/api/v1/configurations/{config_id}/rollback?processing_active=false",
        headers=headers,
    )
    assert rollback_response.status_code == 200
    rollback_body = rollback_response.json()
    assert rollback_body["data"]["status"] == "queued"
