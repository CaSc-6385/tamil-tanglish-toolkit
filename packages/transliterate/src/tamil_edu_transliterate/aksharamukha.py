"""Aksharamukha rule-based Tamil transliteration backend.

Pure Python, no torch/fairseq drama. Quality is rule-based ceiling (CER ~35%
on Tanglish vs. ~10-15% expected from IndicXlit) but works on every Python
version we'll ever target. Substitute for IndicXlit per docs/adr/0002.

Gated behind the `[aksharamukha]` extra:
    uv add 'tamil-edu-transliterate[aksharamukha]'

Tokenization is delegated to the S1-2 code-switch classifier so English /
punctuation / whitespace tokens pass through verbatim.
"""

from __future__ import annotations

from typing import Any

from tamil_edu_transliterate.base import TransliterationError, Word
from tamil_edu_transliterate.tokenizer import TokenKind, tokenize


class AksharamukhaTransliterator:
    """Rule-based Tanglish → Tamil via the aksharamukha library.

    Lazy-loads `aksharamukha.transliterate.process` on first call. If the
    extra is missing, the first call raises TransliterationError with install
    instructions (mirrors IndicXlit's UX).
    """

    name = "aksharamukha"

    def __init__(self, *, scheme: str = "IAST") -> None:
        # IAST is closest to common Tanglish among aksharamukha's input schemes.
        # Itrans introduces too many diacritical artifacts; HK is decent but
        # IAST gives the cleanest output for our golden set.
        self._scheme = scheme
        self._fn: Any | None = None

    def _ensure_fn(self) -> Any:
        if self._fn is not None:
            return self._fn
        try:
            from aksharamukha import transliterate  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover
            raise TransliterationError(
                "Aksharamukha backend requires the 'aksharamukha' extra. Install with: "
                "uv add 'tamil-edu-transliterate[aksharamukha]'"
            ) from exc
        self._fn = transliterate.process
        return self._fn

    def _translit_word(self, word: str) -> str:
        fn = self._ensure_fn()
        try:
            return fn(self._scheme, "Tamil", word)
        except Exception as exc:
            raise TransliterationError(f"Aksharamukha failed on token '{word}': {exc}") from exc

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        if not text:
            return text
        out: list[str] = []
        for tok in tokenize(text):
            if tok.kind == TokenKind.TANGLISH:
                out.append(self._translit_word(tok.text))
            else:
                out.append(tok.text)
        return "".join(out)

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        """Rule-based — only one deterministic output. Returns single-element list."""
        if not text:
            return [text]
        return [self.transliterate(text)]

    def transliterate_detailed(self, text: str, *, topk: int = 3) -> list[Word]:
        if not text:
            return []
        out: list[Word] = []
        for tok in tokenize(text):
            if tok.kind == TokenKind.TANGLISH:
                ta = self._translit_word(tok.text)
                # Rule-based has no real alternatives; expose the chosen as the only one
                out.append(Word(source=tok.text, text=ta, kind=tok.kind, alternatives=[ta]))
            else:
                out.append(Word(source=tok.text, text=tok.text, kind=tok.kind, alternatives=[]))
        return out
