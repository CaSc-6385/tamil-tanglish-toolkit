"""Tamil sentence-structure analysis: per-word POS + gloss + emoji, behind one protocol."""

from __future__ import annotations

from tamil_edu_grammar.base import (
    POS_TAGS,
    Analyzer,
    GrammarError,
    SentenceAnalysis,
    WordAnalysis,
)
from tamil_edu_grammar.ollama import OllamaAnalyzer

__all__ = [
    "POS_TAGS",
    "Analyzer",
    "GrammarError",
    "OllamaAnalyzer",
    "SentenceAnalysis",
    "WordAnalysis",
    "analyze",
]

# Singleton instances, lazy-initialized.
_BACKENDS: dict[str, Analyzer] = {}


def _get(backend: str) -> Analyzer:
    if backend not in _BACKENDS:
        if backend == "ollama":
            _BACKENDS[backend] = OllamaAnalyzer()
        else:
            raise ValueError(f"Unknown grammar backend '{backend}'. Available: ollama")
    return _BACKENDS[backend]


def analyze(text: str, *, backend: str = "ollama") -> SentenceAnalysis:
    """Break a Tamil sentence into a per-word grammar breakdown.

    Args:
        text: a Tamil-script sentence.
        backend: analysis backend (currently only 'ollama').

    Returns:
        A SentenceAnalysis with one WordAnalysis (pos + gloss + emoji) per word.

    Raises:
        ValueError: unknown backend.
        GrammarError: the backend failed.
    """
    return _get(backend).analyze(text)
