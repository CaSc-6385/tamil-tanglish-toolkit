"""Tesseract OCR backend (LSTM engine) via pytesseract.

Reads Tamil + Latin script (lang ``tam+eng``), covering printed-Tamil images and
"Tanglish" images (Tamil written in Roman letters). Dependency-light and CPU-only,
so it fits the Fly.io / Hetzner budget in PLAN.md §8.

Install the extra and ensure the system binary + Tamil data are present::

    uv sync --extra tesseract          # or  pip install tamil-edu-ocr[tesseract]
    brew install tesseract tesseract-lang                  # macOS
    apt-get install tesseract-ocr tesseract-ocr-tam        # Debian/Ubuntu
"""

from __future__ import annotations

import io
import shutil
from typing import TYPE_CHECKING, Any

from tamil_edu_ocr.base import OcrError, OcrLine, OcrResult

if TYPE_CHECKING:
    from PIL import Image

DEFAULT_LANG = "tam+eng"
DEFAULT_PSM = "6"  # assume a single uniform block of text
DEFAULT_MIN_WIDTH = 1000  # upscale small images; Tesseract is best near ~300 DPI


class TesseractOcrEngine:
    """OCR via the system Tesseract binary."""

    name = "tesseract"

    def __init__(
        self,
        *,
        lang: str = DEFAULT_LANG,
        psm: str = DEFAULT_PSM,
        min_width: int = DEFAULT_MIN_WIDTH,
        cmd: str | None = None,
    ) -> None:
        self.lang = lang
        self.psm = psm
        self.min_width = min_width
        self.cmd = cmd

    def _prepare(self, image: bytes) -> Image.Image:
        from PIL import Image, ImageOps

        try:
            img = Image.open(io.BytesIO(image))
            img = ImageOps.exif_transpose(img)
            img = ImageOps.grayscale(img)
            img = ImageOps.autocontrast(img)
        except Exception as exc:  # PIL raises assorted types for bad input
            raise OcrError("Could not read that image file.") from exc
        if img.width < self.min_width:
            scale = self.min_width / img.width
            img = img.resize((self.min_width, max(1, round(img.height * scale))))
        return img

    def read(self, image: bytes) -> OcrResult:
        if not image:
            raise OcrError("Empty image bytes.")
        try:
            import pytesseract
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise OcrError(
                "pytesseract is not installed. Install the 'tesseract' extra: "
                "pip install tamil-edu-ocr[tesseract]"
            ) from exc

        if self.cmd:
            pytesseract.pytesseract.tesseract_cmd = self.cmd
        elif shutil.which(pytesseract.pytesseract.tesseract_cmd) is None:
            found = shutil.which("tesseract")
            if found:
                pytesseract.pytesseract.tesseract_cmd = found

        img = self._prepare(image)
        try:
            data = pytesseract.image_to_data(
                img,
                lang=self.lang,
                config=f"--oem 1 --psm {self.psm}",
                output_type=pytesseract.Output.DICT,
            )
        except Exception as exc:  # tesseract binary missing, bad lang data, etc.
            raise OcrError(f"Tesseract failed: {exc}") from exc

        lines = group_lines(data)
        text = " ".join(line.text for line in lines).strip()
        confs = [line.confidence for line in lines]
        avg = round(sum(confs) / len(confs), 3) if confs else 0.0
        return OcrResult(text=text, lines=lines, avg_confidence=avg, backend=self.name)


def group_lines(data: dict[str, Any]) -> list[OcrLine]:
    """Group Tesseract word boxes into lines with a mean confidence in [0, 1].

    ``data`` is the dict produced by ``pytesseract.image_to_data(..., DICT)``:
    parallel lists keyed by ``text``, ``conf``, ``block_num``, ``par_num``,
    ``line_num``. Words with blank text or negative confidence are dropped.
    """
    buckets: dict[tuple[int, int, int], dict[str, list[Any]]] = {}
    order: list[tuple[int, int, int]] = []
    for i, raw in enumerate(data.get("text", [])):
        word = (raw or "").strip()
        if not word:
            continue
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError, KeyError, IndexError):
            conf = -1.0
        if conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if key not in buckets:
            buckets[key] = {"words": [], "confs": []}
            order.append(key)
        buckets[key]["words"].append(word)
        buckets[key]["confs"].append(conf)

    lines: list[OcrLine] = []
    for key in order:
        bucket = buckets[key]
        line_text = " ".join(bucket["words"]).strip()
        if not line_text:
            continue
        mean = sum(bucket["confs"]) / len(bucket["confs"]) / 100.0
        lines.append(OcrLine(text=line_text, confidence=round(mean, 3)))
    return lines
