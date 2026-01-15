"""Integration test for configuration rollback flow."""

from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_configuration_rollback_flow() -> None:
    """Rollback should restore prior selections as active."""
    headers = {"X-User-Role": "operator"}
    payload_one = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v1"}]}
    payload_two = {"selections": [{"stage_id": "ocr", "module_id": "ocr-v2"}]}

    config_one = client.post("/api/v1/configurations", json=payload_one, headers=headers).json()["data"]["config_id"]
    config_two = client.post("/api/v1/configurations", json=payload_two, headers=headers).json()["data"]["config_id"]

    client.post(f"/api/v1/configurations/{config_two}/activate?processing_active=false", headers=headers)

    rollback_response = client.post(
        f"/api/v1/configurations/{config_one}/rollback?processing_active=false",
        headers=headers,
    )
    assert rollback_response.status_code == 200

    active = client.get("/api/v1/configurations/active").json()["data"]
    assert active["selections"][0]["module_id"] == "ocr-v1"
