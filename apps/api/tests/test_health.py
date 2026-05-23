"""Health endpoint contract tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tamil_edu_api import __version__
from tamil_edu_api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_returns_200(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200


def test_health_payload_shape(client: TestClient) -> None:
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["backend"] in {"baseline", "indicxlit"}
    assert body["version"] == __version__


def test_openapi_docs_available(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "tamil-edu-api"
    assert "/translate" in spec["paths"]
    assert "/health" in spec["paths"]
