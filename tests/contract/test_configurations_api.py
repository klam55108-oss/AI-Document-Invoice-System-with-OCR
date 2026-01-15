"""Contract tests for configuration APIs."""

from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_create_and_validate_configuration_contract() -> None:
    """Create and validate configuration endpoints return expected envelopes."""
    payload = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v1"}]}
    headers = {"X-User-Role": "operator"}

    create_response = client.post("/api/v1/configurations", json=payload, headers=headers)
    assert create_response.status_code == 201
    create_body = create_response.json()
    assert create_body["status"] == "success"
    assert "data" in create_body
    assert "config_id" in create_body["data"]

    validate_response = client.post(
        "/api/v1/configurations/validate", json=payload, headers=headers
    )
    assert validate_response.status_code == 200
    validate_body = validate_response.json()
    assert validate_body["status"] == "success"
    assert "is_valid" in validate_body["data"]


def test_activate_configuration_contract() -> None:
    """Activate configuration returns queued status."""
    payload = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v1"}]}
    headers = {"X-User-Role": "operator"}

    create_response = client.post("/api/v1/configurations", json=payload, headers=headers)
    config_id = create_response.json()["data"]["config_id"]

    activate_response = client.post(
        f"/api/v1/configurations/{config_id}/activate?processing_active=false",
        headers=headers,
    )
    assert activate_response.status_code == 200
    activate_body = activate_response.json()
    assert activate_body["status"] == "success"
    assert activate_body["data"]["status"] == "queued"
