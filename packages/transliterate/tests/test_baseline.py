"""Tests for BaselineTransliterator — the identity passthrough."""

from __future__ import annotations

import pytest
from tamil_edu_transliterate import BaselineTransliterator, Transliterator


def test_baseline_name() -> None:
    assert BaselineTransliterator().name == "baseline"


def test_baseline_returns_input_unchanged() -> None:
    t = BaselineTransliterator()
    assert t.transliterate("vanakkam") == "vanakkam"


def test_baseline_handles_empty_string() -> None:
    assert BaselineTransliterator().transliterate("") == ""


def test_baseline_handles_whitespace_only() -> None:
    assert BaselineTransliterator().transliterate("   ") == "   "


def test_baseline_preserves_multiword_input() -> None:
    t = BaselineTransliterator()
    assert t.transliterate("vanakkam nanba") == "vanakkam nanba"


def test_baseline_preserves_punctuation_and_numbers() -> None:
    t = BaselineTransliterator()
    cases = ["hello, world!", "nalla iruka?", "123 456", "naan #1"]
    for c in cases:
        assert t.transliterate(c) == c


def test_baseline_preserves_unicode_input() -> None:
    """Even though baseline does no transliteration, Tamil input should pass through cleanly."""
    t = BaselineTransliterator()
    assert t.transliterate("வணக்கம்") == "வணக்கம்"


def test_baseline_topk_does_not_change_output() -> None:
    t = BaselineTransliterator()
    assert t.transliterate("hello", topk=1) == t.transliterate("hello", topk=10)


def test_baseline_alternatives_returns_single_element() -> None:
    t = BaselineTransliterator()
    alts = t.alternatives("vanakkam")
    assert alts == ["vanakkam"]


def test_baseline_alternatives_topk_does_not_create_extras() -> None:
    """Baseline has no model; topk doesn't synthesize new alternatives."""
    t = BaselineTransliterator()
    alts = t.alternatives("vanakkam", topk=5)
    assert len(alts) == 1
    assert alts[0] == "vanakkam"


def test_baseline_implements_transliterator_protocol() -> None:
    """Runtime check of the structural type."""
    t = BaselineTransliterator()
    assert isinstance(t, Transliterator)


@pytest.mark.parametrize(
    "text",
    [
        "vanakkam",
        "",
        "   leading and trailing   ",
        "MixedCASE",
        "with-dashes-and_underscores",
        "தமிழ் mixed with English",
    ],
)
def test_baseline_idempotent_for_arbitrary_input(text: str) -> None:
    t = BaselineTransliterator()
    once = t.transliterate(text)
    twice = t.transliterate(once)
    assert once == twice == text
