"""Integration test for configuration activation flow."""

from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_configuration_activation_flow() -> None:
    """Create, activate, and fetch active configuration."""
    headers = {"X-User-Role": "operator"}
    payload = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v1"}]}

    create_response = client.post("/api/v1/configurations", json=payload, headers=headers)
    assert create_response.status_code == 201
    config_id = create_response.json()["data"]["config_id"]

    activate_response = client.post(
        f"/api/v1/configurations/{config_id}/activate?processing_active=false",
        headers=headers,
    )
    assert activate_response.status_code == 200

    active_response = client.get("/api/v1/configurations/active")
    assert active_response.status_code == 200
    active_body = active_response.json()
    assert active_body["data"]["config_id"] == config_id
