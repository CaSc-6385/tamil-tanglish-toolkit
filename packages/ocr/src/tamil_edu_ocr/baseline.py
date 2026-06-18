"""Identity / no-op OCR backend.

Returns an empty result without invoking any OCR engine. Used as:
- The eval lower bound (no text extracted → CER 1.0 against any target).
- A deterministic stand-in for tests / CI boxes that have no Tesseract binary.
"""

from __future__ import annotations

from tamil_edu_ocr.base import OcrError, OcrResult


class BaselineOcrEngine:
    """Performs no OCR. Validates input and returns an empty result."""

    name = "baseline"

    def read(self, image: bytes) -> OcrResult:
        if not image:
            raise OcrError("Empty image bytes.")
        return OcrResult(text="", lines=[], avg_confidence=0.0, backend=self.name)
