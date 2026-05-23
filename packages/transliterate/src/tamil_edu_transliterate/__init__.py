"""Tanglish → Tamil transliteration. Pluggable backends behind a single protocol."""

from __future__ import annotations

from tamil_edu_transliterate.base import TransliterationError, Transliterator
from tamil_edu_transliterate.baseline import BaselineTransliterator
from tamil_edu_transliterate.indicxlit import IndicXlitTransliterator
from tamil_edu_transliterate.tokenizer import Token, TokenKind, tokenize

__all__ = [
    "BaselineTransliterator",
    "IndicXlitTransliterator",
    "Token",
    "TokenKind",
    "TransliterationError",
    "Transliterator",
    "tokenize",
    "transliterate",
]

# Singleton instances, lazy-initialized.
_BACKENDS: dict[str, Transliterator] = {}


def _get(backend: str) -> Transliterator:
    if backend not in _BACKENDS:
        if backend == "baseline":
            _BACKENDS[backend] = BaselineTransliterator()
        elif backend == "indicxlit":
            _BACKENDS[backend] = IndicXlitTransliterator()
        else:
            raise ValueError(f"Unknown backend '{backend}'. Available: baseline, indicxlit")
    return _BACKENDS[backend]


def transliterate(text: str, *, backend: str = "baseline", topk: int = 1) -> str:
    """Convenience function — convert Tanglish to Tamil using the chosen backend.

    Args:
        text: Tanglish input (Roman-script Tamil, optionally with code-switched English).
        backend: 'baseline' (passthrough; default) or 'indicxlit' (requires extras installed).
        topk: number of top candidates the backend considers; the best is returned.

    Returns:
        Tamil Unicode string. For the baseline backend, returns the input unchanged.

    Raises:
        ValueError: unknown backend name.
        TransliterationError: backend failed (e.g. model not installed, runtime error).
    """
    return _get(backend).transliterate(text, topk=topk)
