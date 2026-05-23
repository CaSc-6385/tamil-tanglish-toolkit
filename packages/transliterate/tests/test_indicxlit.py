"""Tests for IndicXlitTransliterator.

The model is ~1GB and pulls torch — most tests here are skipped by default
unless the `indicxlit` extra is installed. The tests that DON'T need the model
(error path when extra isn't installed, tokenization edge cases via the
underlying regex) run unconditionally.
"""

from __future__ import annotations

import importlib.util
from unittest.mock import MagicMock

import pytest
from tamil_edu_transliterate import IndicXlitTransliterator, TransliterationError
from tamil_edu_transliterate.indicxlit import _TOKEN_RE

HAS_AI4BHARAT = importlib.util.find_spec("ai4bharat.transliteration") is not None

requires_indicxlit = pytest.mark.skipif(
    not HAS_AI4BHARAT,
    reason="ai4bharat-transliteration not installed (install with `[indicxlit]` extra)",
)


# ---- Always-runnable tests (no model needed) ----


def test_name() -> None:
    assert IndicXlitTransliterator().name == "indicxlit"


def test_empty_input_returns_empty_without_loading_model() -> None:
    """We never touch the model for empty input — proves laziness."""
    t = IndicXlitTransliterator()
    assert t.transliterate("") == ""
    assert t._engine is None  # ensure no load happened


def test_alternatives_of_empty_input_returns_empty_list_element() -> None:
    t = IndicXlitTransliterator()
    assert t.alternatives("") == [""]
    assert t._engine is None


def test_alternatives_of_punctuation_only_returns_input() -> None:
    t = IndicXlitTransliterator()
    assert t.alternatives("!!!") == ["!!!"]
    assert t._engine is None  # never loaded


def test_token_regex_splits_on_whitespace_preserving_spaces() -> None:
    tokens = _TOKEN_RE.findall("hello world")
    assert tokens == ["hello", " ", "world"]


def test_token_regex_separates_punctuation() -> None:
    tokens = _TOKEN_RE.findall("hi, world!")
    assert tokens == ["hi", ",", " ", "world", "!"]


def test_token_regex_handles_unicode() -> None:
    tokens = _TOKEN_RE.findall("வணக்கம் hello")
    # Tamil word, space, English word
    assert len(tokens) == 3
    assert tokens[0] == "வணக்கம்"
    assert tokens[1] == " "
    assert tokens[2] == "hello"


def test_missing_extra_raises_helpful_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """When ai4bharat-transliteration isn't importable, surface a clear install hint."""
    t = IndicXlitTransliterator()

    # Force the import inside _ensure_engine to fail by injecting None into sys.modules
    import sys

    monkeypatch.setitem(sys.modules, "ai4bharat", None)  # type: ignore[arg-type]
    monkeypatch.setitem(sys.modules, "ai4bharat.transliteration", None)  # type: ignore[arg-type]

    with pytest.raises(TransliterationError, match="indicxlit"):
        t.transliterate("vanakkam")


def test_engine_errors_wrapped_in_transliteration_error() -> None:
    """Any engine.translit_word exception is wrapped — clients catch one type."""
    t = IndicXlitTransliterator()
    mock_engine = MagicMock()
    mock_engine.translit_word.side_effect = RuntimeError("model exploded")
    t._engine = mock_engine

    with pytest.raises(TransliterationError, match="vanakkam"):
        t.transliterate("vanakkam")


def test_engine_empty_result_falls_back_to_input() -> None:
    """If the engine returns {'ta': []} we keep the original token instead of crashing."""
    t = IndicXlitTransliterator()
    mock_engine = MagicMock()
    mock_engine.translit_word.return_value = {"ta": []}
    t._engine = mock_engine

    assert t.transliterate("vanakkam") == "vanakkam"


def test_engine_called_with_input_token() -> None:
    t = IndicXlitTransliterator()
    mock_engine = MagicMock()
    mock_engine.translit_word.return_value = {"ta": ["வணக்கம்"]}
    t._engine = mock_engine

    out = t.transliterate("vanakkam")
    assert out == "வணக்கம்"
    mock_engine.translit_word.assert_called_once()
    args, _ = mock_engine.translit_word.call_args
    assert args[0] == "vanakkam"


def test_punctuation_passthrough_via_mock_engine() -> None:
    t = IndicXlitTransliterator()
    mock_engine = MagicMock()
    mock_engine.translit_word.return_value = {"ta": ["நல்லா"]}
    t._engine = mock_engine

    out = t.transliterate("nalla?")
    assert out == "நல்லா?"  # punctuation preserved
    # Only the word "nalla" should hit the engine; "?" passes through
    assert mock_engine.translit_word.call_count == 1


def test_multiword_assembly_via_mock_engine() -> None:
    t = IndicXlitTransliterator()
    mock_engine = MagicMock()
    mock_engine.translit_word.side_effect = lambda tok, topk=1: {
        "ta": {"vanakkam": ["வணக்கம்"], "nanba": ["நண்பா"]}.get(tok, [tok])
    }
    t._engine = mock_engine

    assert t.transliterate("vanakkam nanba") == "வணக்கம் நண்பா"


def test_alternatives_varies_first_word_via_mock_engine() -> None:
    t = IndicXlitTransliterator()
    mock_engine = MagicMock()

    def fake(tok: str, topk: int = 1) -> dict[str, list[str]]:
        if tok == "vanakkam":
            return {"ta": ["வணக்கம்", "வாணக்கம்", "வணக்கமா"]}
        return {"ta": [tok]}

    mock_engine.translit_word.side_effect = fake
    t._engine = mock_engine

    alts = t.alternatives("vanakkam", topk=3)
    assert alts == ["வணக்கம்", "வாணக்கம்", "வணக்கமா"]


# ---- Real-model tests (skipped without `[indicxlit]` extra) ----


@requires_indicxlit
def test_real_engine_translates_vanakkam() -> None:
    """End-to-end check against the actual model. Slow on first run (model load)."""
    t = IndicXlitTransliterator()
    out = t.transliterate("vanakkam")
    # We can't assert exact equality without coupling to the model; assert script class.
    assert any("஀" <= ch <= "௿" for ch in out), f"expected Tamil script in {out!r}"


@requires_indicxlit
def test_real_engine_handles_multiword() -> None:
    t = IndicXlitTransliterator()
    out = t.transliterate("nalla iruka")
    assert " " in out
    assert any("஀" <= ch <= "௿" for ch in out)
