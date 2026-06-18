"""Protocol + shared types for OCR backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class OcrError(RuntimeError):
    """Raised when an OCR backend fails (engine missing, unreadable image, crash)."""


@dataclass(frozen=True)
class OcrLine:
    """One detected line of text with a mean confidence in [0.0, 1.0]."""

    text: str
    confidence: float


@dataclass(frozen=True)
class OcrResult:
    """Full OCR output: the joined text, per-line detail, and the backend used.

    Reassembly: ``" ".join(line.text for line in lines)`` (then stripped) equals
    ``text``.
    """

    text: str
    lines: list[OcrLine] = field(default_factory=list)
    avg_confidence: float = 0.0
    backend: str = ""


@runtime_checkable
class OcrEngine(Protocol):
    """Public contract every OCR backend implements.

    Construction must be cheap — heavy setup (locating the Tesseract binary,
    loading a model) belongs in the first ``read()`` call, not ``__init__``.
    """

    name: str

    def read(self, image: bytes) -> OcrResult:
        """Extract text from raw image bytes (PNG / JPEG / WEBP / ...).

        Args:
            image: the raw bytes of an image file.

        Raises:
            OcrError: the image is empty/unreadable or the engine failed.
        """
        ...
