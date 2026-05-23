"""Identity passthrough transliterator.

Used as:
- The eval baseline (`eval/run.py` --model baseline) — produces near-1.0 CER
  against Tamil targets, which is the meaningful lower bound to beat.
- A fast stand-in for tests where you need a Transliterator but don't want
  to load an ML model.
"""

from __future__ import annotations

from tamil_edu_transliterate.base import Word
from tamil_edu_transliterate.tokenizer import tokenize


class BaselineTransliterator:
    """Returns input unchanged. No transliteration is performed."""

    name = "baseline"

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        return text

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        return [text]

    def transliterate_detailed(self, text: str, *, topk: int = 3) -> list[Word]:
        if not text:
            return []
        return [
            Word(source=tok.text, text=tok.text, kind=tok.kind, alternatives=[])
            for tok in tokenize(text)
        ]
