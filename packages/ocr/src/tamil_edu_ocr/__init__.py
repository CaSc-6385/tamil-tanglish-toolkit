"""Image OCR for printed Tamil / Tanglish. Pluggable backends behind one protocol."""

from __future__ import annotations

from tamil_edu_ocr.base import OcrEngine, OcrError, OcrLine, OcrResult
from tamil_edu_ocr.baseline import BaselineOcrEngine
from tamil_edu_ocr.tesseract import TesseractOcrEngine

__all__ = [
    "BaselineOcrEngine",
    "OcrEngine",
    "OcrError",
    "OcrLine",
    "OcrResult",
    "TesseractOcrEngine",
    "ocr",
]

# Singleton instances, lazy-initialized.
_ENGINES: dict[str, OcrEngine] = {}


def _get(backend: str) -> OcrEngine:
    if backend not in _ENGINES:
        if backend == "baseline":
            _ENGINES[backend] = BaselineOcrEngine()
        elif backend in ("tesseract", "tess"):
            _ENGINES[backend] = TesseractOcrEngine()
        else:
            raise ValueError(f"Unknown OCR backend '{backend}'. Available: baseline, tesseract")
    return _ENGINES[backend]


def ocr(image: bytes, *, backend: str = "tesseract") -> OcrResult:
    """Extract text from image bytes using the chosen backend.

    Args:
        image: raw image bytes (PNG / JPEG / WEBP / ...).
        backend: 'tesseract' (default; needs the tesseract binary + the
            'tesseract' extra) or 'baseline' (no-op, returns empty — for tests/eval).

    Returns:
        An OcrResult with the joined text, per-line detail, and average confidence.

    Raises:
        ValueError: unknown backend name.
        OcrError: image unreadable or the engine failed.
    """
    return _get(backend).read(image)
