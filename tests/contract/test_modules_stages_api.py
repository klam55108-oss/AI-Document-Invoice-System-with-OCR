"""Contract tests for modules and stages APIs."""

from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_list_modules_contract() -> None:
    """Modules endpoint returns success envelope."""
    response = client.get("/api/v1/modules")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert isinstance(payload["data"], list)


def test_list_stages_contract() -> None:
    """Stages endpoint returns success envelope."""
    response = client.get("/api/v1/stages")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert isinstance(payload["data"], list)
