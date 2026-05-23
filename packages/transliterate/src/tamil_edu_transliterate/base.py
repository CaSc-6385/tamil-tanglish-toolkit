"""Protocol + shared types for transliteration backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from tamil_edu_transliterate.tokenizer import TokenKind


class TransliterationError(RuntimeError):
    """Raised when a backend fails (e.g. model not installed, model crashed)."""


@dataclass(frozen=True)
class Word:
    """Per-token output of a detailed transliteration.

    Examples:
        Tanglish input "vanakkam" → Word(source="vanakkam", text="வணக்கம்",
            kind=TANGLISH, alternatives=["வணக்கம்", "வாணக்கம்"]).
        English input "send" → Word(source="send", text="send", kind=ENGLISH,
            alternatives=[]).
        Whitespace " " → Word(source=" ", text=" ", kind=WHITESPACE, alternatives=[]).
    """

    source: str
    text: str
    kind: TokenKind
    alternatives: list[str] = field(default_factory=list)


@runtime_checkable
class Transliterator(Protocol):
    """Public contract every backend implements.

    Implementations must be safe to call concurrently AFTER any one-time setup
    (e.g. model load) completes. They should be cheap to construct — heavy
    initialisation (loading a 1GB model) belongs in the first `transliterate()`
    call, not in `__init__`.
    """

    name: str

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        """Convert Tanglish to Tamil. Returns the single best candidate.

        Args:
            text: input. May be empty, whitespace-only, multi-word, code-switched.
            topk: number of internal candidates the backend evaluates. Higher
                = potentially better quality, slower. Final return is still one string.
        """
        ...

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        """Return the top-K candidate Tamil transliterations of the whole input,
        best first.

        For backends that don't produce alternatives (baseline), this returns
        a single-element list containing whatever `transliterate()` returns.
        """
        ...

    def transliterate_detailed(self, text: str, *, topk: int = 3) -> list[Word]:
        """Per-token transliteration with alternatives.

        Reassembly: ``"".join(w.text for w in result)`` equals the transliterated
        whole-string output.

        Each Word includes the original source token, the chosen text, the
        token kind from the code-switch classifier, and up to ``topk``
        alternatives for tokens that come from the ML backend. English /
        whitespace / punctuation tokens have empty alternatives.
        """
        ...
