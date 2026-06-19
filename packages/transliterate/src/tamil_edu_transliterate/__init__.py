"""Tanglish → Tamil transliteration. Pluggable backends behind a single protocol."""

from __future__ import annotations

from tamil_edu_transliterate.aksharamukha import AksharamukhaTransliterator
from tamil_edu_transliterate.base import TransliterationError, Transliterator, Word
from tamil_edu_transliterate.baseline import BaselineTransliterator
from tamil_edu_transliterate.indicxlit import IndicXlitTransliterator
from tamil_edu_transliterate.ollama import OllamaTransliterator
from tamil_edu_transliterate.openai_gpt import OpenAiGptTransliterator
from tamil_edu_transliterate.sarvam import SarvamTransliterator
from tamil_edu_transliterate.tokenizer import Token, TokenKind, tokenize

__all__ = [
    "AksharamukhaTransliterator",
    "BaselineTransliterator",
    "IndicXlitTransliterator",
    "OllamaTransliterator",
    "OpenAiGptTransliterator",
    "SarvamTransliterator",
    "Token",
    "TokenKind",
    "TransliterationError",
    "Transliterator",
    "Word",
    "tokenize",
    "transliterate",
]

# Singleton instances, lazy-initialized.
_BACKENDS: dict[str, Transliterator] = {}


def _get(backend: str) -> Transliterator:
    if backend not in _BACKENDS:
        if backend == "baseline":
            _BACKENDS[backend] = BaselineTransliterator()
        elif backend == "aksharamukha":
            _BACKENDS[backend] = AksharamukhaTransliterator()
        elif backend == "indicxlit":
            _BACKENDS[backend] = IndicXlitTransliterator()
        elif backend in ("ollama", "ollama-tamil"):
            _BACKENDS[backend] = OllamaTransliterator()
        elif backend in ("sarvam", "sarvam-translate"):
            _BACKENDS[backend] = SarvamTransliterator()
        elif backend in ("openai-gpt", "openai_gpt", "openai"):
            _BACKENDS[backend] = OpenAiGptTransliterator()
        else:
            raise ValueError(
                f"Unknown backend '{backend}'. "
                "Available: baseline, aksharamukha, ollama, openai-gpt, indicxlit"
            )
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
