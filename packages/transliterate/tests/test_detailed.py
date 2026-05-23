"""Tests for the per-word `transliterate_detailed()` API."""

from __future__ import annotations

from unittest.mock import MagicMock

from tamil_edu_transliterate import (
    BaselineTransliterator,
    IndicXlitTransliterator,
    TokenKind,
    Word,
)

# ---- Baseline ----


def test_baseline_detailed_empty_returns_empty() -> None:
    assert BaselineTransliterator().transliterate_detailed("") == []


def test_baseline_detailed_single_word() -> None:
    words = BaselineTransliterator().transliterate_detailed("vanakkam")
    assert words == [Word(source="vanakkam", text="vanakkam", kind=TokenKind.TANGLISH)]


def test_baseline_detailed_preserves_round_trip() -> None:
    text = "send the message ku reply pannu"
    words = BaselineTransliterator().transliterate_detailed(text)
    rebuilt = "".join(w.text for w in words)
    assert rebuilt == text


def test_baseline_detailed_classifies_kinds() -> None:
    words = BaselineTransliterator().transliterate_detailed("send vanakkam")
    by_text = {w.source: w.kind for w in words if w.kind in (TokenKind.ENGLISH, TokenKind.TANGLISH)}
    assert by_text == {"send": TokenKind.ENGLISH, "vanakkam": TokenKind.TANGLISH}


def test_baseline_detailed_alternatives_always_empty() -> None:
    words = BaselineTransliterator().transliterate_detailed("vanakkam nanba")
    assert all(w.alternatives == [] for w in words)


# ---- IndicXlit (mocked engine, no model load) ----


def test_indicxlit_detailed_empty_returns_empty() -> None:
    assert IndicXlitTransliterator().transliterate_detailed("") == []


def test_indicxlit_detailed_single_tanglish_word_uses_engine_alternatives() -> None:
    t = IndicXlitTransliterator()
    mock = MagicMock()
    mock.translit_word.return_value = {"ta": ["வணக்கம்", "வாணக்கம்", "வணக்கமா"]}
    t._engine = mock

    words = t.transliterate_detailed("vanakkam", topk=3)
    assert len(words) == 1
    w = words[0]
    assert w.source == "vanakkam"
    assert w.text == "வணக்கம்"
    assert w.kind == TokenKind.TANGLISH
    assert w.alternatives == ["வணக்கம்", "வாணக்கம்", "வணக்கமா"]


def test_indicxlit_detailed_english_preserved_with_empty_alternatives() -> None:
    t = IndicXlitTransliterator()
    mock = MagicMock()
    mock.translit_word.return_value = {"ta": ["வணக்கம்"]}
    t._engine = mock

    words = t.transliterate_detailed("send vanakkam")
    by_source = {w.source: w for w in words if w.kind in (TokenKind.ENGLISH, TokenKind.TANGLISH)}

    assert by_source["send"].text == "send"
    assert by_source["send"].kind == TokenKind.ENGLISH
    assert by_source["send"].alternatives == []

    assert by_source["vanakkam"].text == "வணக்கம்"
    assert by_source["vanakkam"].kind == TokenKind.TANGLISH


def test_indicxlit_detailed_round_trip_via_text_field() -> None:
    """Joining word.text reproduces the same output as transliterate()."""
    t = IndicXlitTransliterator()
    mock = MagicMock()
    mock.translit_word.side_effect = lambda tok, topk=1: {
        "ta": {"vanakkam": ["வணக்கம்"], "nanba": ["நண்பா"]}.get(tok, [tok])
    }
    t._engine = mock

    text = "vanakkam nanba"
    detailed = t.transliterate_detailed(text)
    rebuilt = "".join(w.text for w in detailed)
    assert rebuilt == t.transliterate(text)


def test_indicxlit_detailed_respects_topk() -> None:
    t = IndicXlitTransliterator()
    mock = MagicMock()
    mock.translit_word.return_value = {"ta": ["a", "b", "c", "d", "e"]}
    t._engine = mock

    words = t.transliterate_detailed("vanakkam", topk=3)
    assert len(words[0].alternatives) == 3
    assert words[0].alternatives == ["a", "b", "c"]


def test_indicxlit_detailed_whitespace_separator_preserved() -> None:
    t = IndicXlitTransliterator()
    mock = MagicMock()
    mock.translit_word.return_value = {"ta": ["X"]}
    t._engine = mock

    words = t.transliterate_detailed("a b")
    kinds = [w.kind for w in words]
    assert TokenKind.WHITESPACE in kinds


def test_indicxlit_detailed_punctuation_preserved() -> None:
    t = IndicXlitTransliterator()
    mock = MagicMock()
    mock.translit_word.return_value = {"ta": ["நல்லா"]}
    t._engine = mock

    words = t.transliterate_detailed("nalla?")
    by_kind = {w.kind: w.text for w in words}
    assert by_kind[TokenKind.PUNCTUATION] == "?"
    assert by_kind[TokenKind.TANGLISH] == "நல்லா"
