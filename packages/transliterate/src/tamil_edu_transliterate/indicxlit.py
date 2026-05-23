"""IndicXlit (ai4bharat) Tamil transliteration backend.

The model is ~1GB and pulls in PyTorch — it is gated behind the `indicxlit` extra:
    uv add 'tamil-edu-transliterate[indicxlit]'

The XlitEngine works at the WORD level, so this wrapper tokenizes the input
on whitespace, runs each token through the engine, and reassembles. Punctuation
and code-switched English (per S1-2) will be handled by an upstream tokenizer
in a future iteration; for now, all whitespace-separated tokens are sent to
the engine and it returns sensible passthroughs for English-only tokens.

Reference: https://github.com/AI4Bharat/IndicXlit
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from tamil_edu_transliterate.base import TransliterationError

if TYPE_CHECKING:
    pass

# Split keeping the whitespace + punctuation as separators so we can reassemble
# the output preserving the original spacing. Matches one or more non-space chars
# OR one or more whitespace chars OR a single punctuation character.
_TOKEN_RE = re.compile(r"\s+|[^\w\s]|\w+", flags=re.UNICODE)


class IndicXlitTransliterator:
    """Wrap `ai4bharat.transliteration.XlitEngine` for Tamil.

    The engine is loaded on first call (lazy). If `ai4bharat-transliteration`
    is not installed, the first call raises TransliterationError with install
    instructions instead of crashing with ImportError.
    """

    name = "indicxlit"

    def __init__(self, *, beam_width: int = 10) -> None:
        self._beam_width = beam_width
        self._engine: Any | None = None

    def _ensure_engine(self) -> Any:
        if self._engine is not None:
            return self._engine
        try:
            from ai4bharat.transliteration import XlitEngine
        except ImportError as exc:  # pragma: no cover — exercised only without extras
            raise TransliterationError(
                "IndicXlit backend requires the 'indicxlit' extra. Install with: "
                "uv add 'tamil-edu-transliterate[indicxlit]'"
            ) from exc

        self._engine = XlitEngine(
            "ta",
            beam_width=self._beam_width,
            src_script_type="en",
        )
        return self._engine

    def _translit_token(self, token: str, topk: int) -> list[str]:
        """Transliterate a single word token; return ranked candidates."""
        if not token or not token.isalpha():
            # punctuation, digits, or empty — pass through unchanged
            return [token]
        engine = self._ensure_engine()
        try:
            result = engine.translit_word(token, topk=max(topk, 1))
        except Exception as exc:
            raise TransliterationError(f"IndicXlit failed on token '{token}': {exc}") from exc
        candidates = result.get("ta", []) if isinstance(result, dict) else []
        if not candidates:
            return [token]
        return list(candidates)

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        if not text:
            return text
        tokens = _TOKEN_RE.findall(text)
        out: list[str] = []
        for tok in tokens:
            if tok.isspace() or not tok.isalpha():
                out.append(tok)
                continue
            candidates = self._translit_token(tok, topk)
            out.append(candidates[0])
        return "".join(out)

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        """Return top-K transliterations of the whole input.

        Generates the cartesian product would explode for long inputs; we limit
        to varying the FIRST word's candidates and keeping the rest of the
        sentence at top-1. This is a good-enough alternatives UX for single
        words and short phrases.
        """
        if not text:
            return [text]
        tokens = _TOKEN_RE.findall(text)
        # Find the first alphabetic token; vary its candidates.
        first_alpha_idx = next(
            (i for i, t in enumerate(tokens) if t.isalpha()),
            None,
        )
        if first_alpha_idx is None:
            return [text]
        first_candidates = self._translit_token(tokens[first_alpha_idx], topk)
        results: list[str] = []
        for cand in first_candidates[:topk]:
            assembled = []
            for i, tok in enumerate(tokens):
                if i == first_alpha_idx:
                    assembled.append(cand)
                elif tok.isspace() or not tok.isalpha():
                    assembled.append(tok)
                else:
                    rest = self._translit_token(tok, 1)
                    assembled.append(rest[0])
            results.append("".join(assembled))
        return results
