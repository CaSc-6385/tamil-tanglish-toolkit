"""Contract tests for POST /translate."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tamil_edu_api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_translate_baseline_round_trip(client: TestClient) -> None:
    r = client.post("/translate", json={"text": "vanakkam"})
    assert r.status_code == 200
    body = r.json()
    assert body["tamil"] == "vanakkam"  # baseline passthrough
    assert body["backend"] == "baseline"


def test_translate_empty_string_is_ok(client: TestClient) -> None:
    r = client.post("/translate", json={"text": ""})
    assert r.status_code == 200
    assert r.json()["tamil"] == ""


def test_translate_includes_duration(client: TestClient) -> None:
    body = client.post("/translate", json={"text": "hi"}).json()
    assert "duration_ms" in body
    assert isinstance(body["duration_ms"], int)
    assert body["duration_ms"] >= 0


def test_translate_alternatives_returned_when_topk_gt_1(client: TestClient) -> None:
    body = client.post("/translate", json={"text": "vanakkam", "topk": 3}).json()
    assert isinstance(body["alternatives"], list)
    assert len(body["alternatives"]) >= 1


def test_translate_no_alternatives_for_topk_1(client: TestClient) -> None:
    body = client.post("/translate", json={"text": "vanakkam", "topk": 1}).json()
    # alternatives may be [] or [single] — both acceptable
    assert isinstance(body["alternatives"], list)


def test_translate_rejects_topk_below_1(client: TestClient) -> None:
    r = client.post("/translate", json={"text": "hi", "topk": 0})
    assert r.status_code == 422


def test_translate_rejects_topk_above_10(client: TestClient) -> None:
    r = client.post("/translate", json={"text": "hi", "topk": 11})
    assert r.status_code == 422


def test_translate_rejects_oversized_text(client: TestClient) -> None:
    r = client.post("/translate", json={"text": "x" * 2001})
    assert r.status_code == 422


def test_translate_rejects_missing_text_field(client: TestClient) -> None:
    r = client.post("/translate", json={})
    assert r.status_code == 422


def test_translate_preserves_code_switched_english(client: TestClient) -> None:
    """Baseline passes everything through, so English words come back identical."""
    payload = "send the WhatsApp message"
    body = client.post("/translate", json={"text": payload}).json()
    assert body["tamil"] == payload


def test_translate_unicode_input_does_not_error(client: TestClient) -> None:
    """Tamil input should pass through baseline unchanged."""
    body = client.post("/translate", json={"text": "வணக்கம்"}).json()
    assert body["tamil"] == "வணக்கம்"


def test_cors_preflight_allows_localhost_3000(client: TestClient) -> None:
    r = client.options(
        "/translate",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
