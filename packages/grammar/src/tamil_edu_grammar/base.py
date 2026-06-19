"""Protocol + shared types for the grammar / sentence-structure analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# Kid-friendly part-of-speech tags (a simplified Universal-Dependencies set). The
# web UI colour-codes each one and shows the emoji as a picture cue.
POS_TAGS = frozenset(
    {
        "noun",
        "verb",
        "adjective",
        "adverb",
        "pronoun",
        "postposition",
        "conjunction",
        "numeral",
        "particle",
        "other",
    }
)


class GrammarError(RuntimeError):
    """Raised when an analysis backend fails (model unreachable, bad output)."""


@dataclass(frozen=True)
class WordAnalysis:
    """One analysed word of a Tamil sentence."""

    tamil: str
    pos: str  # one of POS_TAGS
    gloss: str  # short English meaning, e.g. "book"
    emoji: str = ""  # a single picture emoji for concrete words, else ""


@dataclass(frozen=True)
class SentenceAnalysis:
    """Full word-by-word breakdown of a Tamil sentence."""

    tamil: str
    words: list[WordAnalysis] = field(default_factory=list)
    model: str = ""


@runtime_checkable
class Analyzer(Protocol):
    """Public contract every grammar backend implements."""

    name: str

    def analyze(self, text: str) -> SentenceAnalysis:
        """Break a Tamil sentence into per-word POS + gloss + emoji.

        Raises:
            GrammarError: the backend failed.
        """
        ...
