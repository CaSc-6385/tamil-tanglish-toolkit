"""Tests for OpenAiGptTransliterator (mocked — no real API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from tamil_edu_transliterate import OpenAiGptTransliterator, TransliterationError


def _fake_resp(*contents: str):
    resp = MagicMock()
    resp.choices = []
    for c in contents:
        choice = MagicMock()
        choice.message.content = c
        resp.choices.append(choice)
    return resp


def test_name() -> None:
    assert OpenAiGptTransliterator().name == "openai-gpt"


def test_empty_input_returns_empty_without_calling_api() -> None:
    t = OpenAiGptTransliterator()
    assert t.transliterate("") == ""
    assert t._client is None


def test_alternatives_of_empty_input_returns_single() -> None:
    t = OpenAiGptTransliterator()
    assert t.alternatives("") == [""]


def test_transliterate_calls_api_and_returns_content() -> None:
    t = OpenAiGptTransliterator()
    mock = MagicMock()
    mock.chat.completions.create.return_value = _fake_resp("வணக்கம்")
    t._client = mock

    out = t.transliterate("vanakkam")
    assert out == "வணக்கம்"
    mock.chat.completions.create.assert_called_once()
    kwargs = mock.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["temperature"] == 0.0
    assert kwargs["n"] == 1


def test_alternatives_uses_higher_temperature_and_n() -> None:
    t = OpenAiGptTransliterator()
    mock = MagicMock()
    mock.chat.completions.create.return_value = _fake_resp("வணக்கம்", "வாணக்கம்", "வணக்கமா")
    t._client = mock

    alts = t.alternatives("vanakkam", topk=3)
    assert alts == ["வணக்கம்", "வாணக்கம்", "வணக்கமா"]
    kwargs = mock.chat.completions.create.call_args.kwargs
    assert kwargs["n"] == 3
    assert kwargs["temperature"] > 0


def test_alternatives_topk_capped_at_3() -> None:
    t = OpenAiGptTransliterator()
    mock = MagicMock()
    mock.chat.completions.create.return_value = _fake_resp("a", "b", "c")
    t._client = mock
    t.alternatives("x", topk=10)
    assert mock.chat.completions.create.call_args.kwargs["n"] == 3


def test_missing_api_key_raises_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Pretend openai is importable so we hit the key check
    import sys

    fake_openai = MagicMock()
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    t = OpenAiGptTransliterator()
    with pytest.raises(TransliterationError, match="OPENAI_API_KEY"):
        t.transliterate("vanakkam")


def test_api_error_wrapped_in_transliteration_error() -> None:
    t = OpenAiGptTransliterator()
    mock = MagicMock()
    mock.chat.completions.create.side_effect = RuntimeError("rate limited")
    t._client = mock

    with pytest.raises(TransliterationError, match="OpenAI API call failed"):
        t.transliterate("vanakkam")


def test_transliterate_detailed_with_pure_tanglish() -> None:
    t = OpenAiGptTransliterator()
    mock = MagicMock()
    mock.chat.completions.create.return_value = _fake_resp("வணக்கம்")
    t._client = mock

    words = t.transliterate_detailed("vanakkam")
    # Pure Tanglish input → alignment may simplify to single Word with full output
    assert len(words) >= 1
    rebuilt = "".join(w.text for w in words)
    assert rebuilt == "வணக்கம்"


def test_aksharamukha_strips_grantha_digit_marks() -> None:
    """Cosmetic cleanup: ¹²³⁴ aspiration markers don't belong in modern Tamil."""
    from tamil_edu_transliterate import AksharamukhaTransliterator

    t = AksharamukhaTransliterator()
    mock = MagicMock(return_value="நந்த்³ரி")
    t._fn = mock
    out = t.transliterate("nandri")
    assert "³" not in out
    assert "²" not in out
    assert out == "நந்த்ரி"
