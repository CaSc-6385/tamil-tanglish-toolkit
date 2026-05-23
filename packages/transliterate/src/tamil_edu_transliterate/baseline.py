"""Identity passthrough transliterator.

Used as:
- The eval baseline (`eval/run.py` --model baseline) — produces near-1.0 CER
  against Tamil targets, which is the meaningful lower bound to beat.
- A fast stand-in for tests where you need a Transliterator but don't want
  to load an ML model.
"""

from __future__ import annotations


class BaselineTransliterator:
    """Returns input unchanged. No transliteration is performed."""

    name = "baseline"

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        return text

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        return [text]
