"""Performance checks for configuration endpoints."""

import time

from fastapi.testclient import TestClient

from interface.api.main import app

client = TestClient(app)


def test_configuration_list_performance() -> None:
    """List configurations responds within acceptable bounds."""
    start = time.perf_counter()
    response = client.get("/api/v1/configurations")
    duration = time.perf_counter() - start

    assert response.status_code == 200
    assert duration < 2.0
