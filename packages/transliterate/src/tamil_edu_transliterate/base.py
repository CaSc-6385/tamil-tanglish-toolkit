"""Protocol + shared types for transliteration backends."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


class TransliterationError(RuntimeError):
    """Raised when a backend fails (e.g. model not installed, model crashed)."""


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
        """Return the top-K candidate Tamil transliterations, best first.

        For backends that don't produce alternatives (baseline), this returns
        a single-element list containing whatever `transliterate()` returns.
        """
        ...
