"""Tests for the Tesseract backend.

The Tesseract *binary* is not required: ``image_to_data`` is monkeypatched so the
line-grouping and result-assembly logic is covered deterministically. A single
live smoke test runs only when the binary is actually installed.
"""

from __future__ import annotations

import io
import shutil

import pytest
from tamil_edu_ocr import OcrError, TesseractOcrEngine
from tamil_edu_ocr.tesseract import group_lines

# A canned pytesseract.image_to_data(DICT) payload: two lines across two blocks,
# with one blank word and one negative-confidence word that must be dropped.
CANNED = {
    "text": ["வணக்கம்", "தமிழ்", "", "naan", "tamil"],
    "conf": [92.0, 88.0, -1, 95.0, 90.0],
    "block_num": [1, 1, 1, 2, 2],
    "par_num": [1, 1, 1, 1, 1],
    "line_num": [1, 1, 2, 1, 1],
}


def _png_bytes(width: int = 320, height: int = 80) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (width, height), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_group_lines_groups_words_and_averages_confidence() -> None:
    lines = group_lines(CANNED)
    assert [line.text for line in lines] == ["வணக்கம் தமிழ்", "naan tamil"]
    assert lines[0].confidence == pytest.approx((92 + 88) / 2 / 100)
    assert lines[1].confidence == pytest.approx((95 + 90) / 2 / 100)


def test_group_lines_drops_blank_and_negative_conf_tokens() -> None:
    # 5 raw tokens in CANNED, but blank + conf=-1 are removed -> 2 grouped lines.
    assert len(group_lines(CANNED)) == 2


def test_group_lines_handles_empty_payload() -> None:
    assert group_lines({"text": []}) == []


def test_read_with_mocked_tesseract(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PIL")
    pytesseract = pytest.importorskip("pytesseract")
    monkeypatch.setattr(pytesseract, "image_to_data", lambda *a, **k: CANNED)

    res = TesseractOcrEngine().read(_png_bytes())
    assert res.backend == "tesseract"
    assert "வணக்கம் தமிழ்" in res.text
    assert "naan tamil" in res.text
    assert 0.0 < res.avg_confidence <= 1.0
    assert len(res.lines) == 2


def test_read_rejects_empty_bytes() -> None:
    with pytest.raises(OcrError):
        TesseractOcrEngine().read(b"")


def test_read_rejects_unreadable_image() -> None:
    pytest.importorskip("pytesseract")
    pytest.importorskip("PIL")
    with pytest.raises(OcrError):
        TesseractOcrEngine().read(b"this is definitely not an image")


def test_read_wraps_tesseract_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("PIL")
    pytesseract = pytest.importorskip("pytesseract")

    def boom(*_a: object, **_k: object) -> dict[str, list[object]]:
        raise RuntimeError("tesseract binary missing")

    monkeypatch.setattr(pytesseract, "image_to_data", boom)
    with pytest.raises(OcrError, match="Tesseract failed"):
        TesseractOcrEngine().read(_png_bytes())


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract binary not installed")
def test_live_tesseract_smoke() -> None:
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (600, 120), "white")
    ImageDraw.Draw(img).text((20, 40), "naan tamil padikiren", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    res = TesseractOcrEngine().read(buf.getvalue())
    assert res.backend == "tesseract"
    assert isinstance(res.text, str)
