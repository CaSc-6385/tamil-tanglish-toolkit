"""Contract tests for POST /ocr."""

from __future__ import annotations

import io

import pytest
import tamil_edu_api.main as main
from fastapi.testclient import TestClient
from tamil_edu_api.main import app
from tamil_edu_ocr import OcrError, OcrLine, OcrResult


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _png_bytes() -> bytes:
    pytest.importorskip("PIL")
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (120, 40), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_ocr_baseline_returns_shape(client: TestClient) -> None:
    files = {"image": ("blank.png", _png_bytes(), "image/png")}
    r = client.post("/ocr", files=files)
    assert r.status_code == 200
    body = r.json()
    assert set(body) >= {"text", "lines", "avg_confidence", "backend", "duration_ms"}
    assert body["backend"] == "baseline"  # pinned in conftest
    assert isinstance(body["lines"], list)
    assert isinstance(body["duration_ms"], int)
    assert body["duration_ms"] >= 0


def test_ocr_rejects_missing_file(client: TestClient) -> None:
    r = client.post("/ocr")
    assert r.status_code == 422  # FastAPI validation: required UploadFile missing


def test_ocr_rejects_empty_upload(client: TestClient) -> None:
    files = {"image": ("empty.png", b"", "image/png")}
    r = client.post("/ocr", files=files)
    assert r.status_code == 400


def test_ocr_rejects_unsupported_type(client: TestClient) -> None:
    files = {"image": ("note.txt", b"hello", "text/plain")}
    r = client.post("/ocr", files=files)
    assert r.status_code == 415


def test_ocr_rejects_oversized_image(client: TestClient) -> None:
    big = b"\x89PNG\r\n" + b"0" * (10 * 1024 * 1024 + 1)
    files = {"image": ("big.png", big, "image/png")}
    r = client.post("/ocr", files=files)
    assert r.status_code == 413


def test_ocr_success_path_with_extracted_text(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Monkeypatch the OCR call so we can assert a real text-bearing response
    without depending on the Tesseract binary."""

    def fake_ocr(_data: bytes, *, backend: str) -> OcrResult:
        return OcrResult(
            text="naan tamil padikiren",
            lines=[OcrLine(text="naan tamil padikiren", confidence=0.93)],
            avg_confidence=0.93,
            backend="tesseract",
        )

    monkeypatch.setattr(main, "run_ocr", fake_ocr)
    files = {"image": ("note.png", _png_bytes(), "image/png")}
    body = client.post("/ocr", files=files).json()
    assert body["text"] == "naan tamil padikiren"
    assert body["lines"][0]["confidence"] == pytest.approx(0.93)
    assert body["avg_confidence"] == pytest.approx(0.93)


def test_ocr_engine_error_returns_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_data: bytes, *, backend: str) -> object:
        raise OcrError("Could not read that image file.")

    monkeypatch.setattr(main, "run_ocr", boom)
    files = {"image": ("bad.png", _png_bytes(), "image/png")}
    r = client.post("/ocr", files=files)
    assert r.status_code == 422
