"""Tests for the no-op baseline OCR backend and the dispatch entry point."""

from __future__ import annotations

import pytest
from tamil_edu_ocr import BaselineOcrEngine, OcrError, OcrResult, ocr


def test_baseline_returns_empty_result() -> None:
    res = BaselineOcrEngine().read(b"non-empty-but-not-a-real-image")
    assert isinstance(res, OcrResult)
    assert res.text == ""
    assert res.lines == []
    assert res.avg_confidence == 0.0
    assert res.backend == "baseline"


def test_baseline_rejects_empty_bytes() -> None:
    with pytest.raises(OcrError):
        BaselineOcrEngine().read(b"")


def test_ocr_dispatch_to_baseline() -> None:
    res = ocr(b"abc", backend="baseline")
    assert res.backend == "baseline"


def test_ocr_unknown_backend_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown OCR backend"):
        ocr(b"abc", backend="does-not-exist")
