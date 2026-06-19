"""Tests for the Ollama grammar analyzer — urlopen mocked, no live server needed."""

from __future__ import annotations

import json
import urllib.error

import pytest
from tamil_edu_grammar import GrammarError, OllamaAnalyzer, SentenceAnalysis, analyze
from tamil_edu_grammar.ollama import _parse_words

_GOOD_JSON = (
    "Here is the breakdown: ["
    '{"tamil":"நான்","pos":"pronoun","gloss":"I","emoji":"🙋"},'
    '{"tamil":"புத்தகம்","pos":"noun","gloss":"book","emoji":"📖"},'
    '{"tamil":"படிக்கிறேன்","pos":"VERB","gloss":"read","emoji":"📚"}]'
)


class _FakeResp:
    def __init__(self, payload: dict[str, object]) -> None:
        self._data = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> _FakeResp:
        return self

    def __exit__(self, *_a: object) -> bool:
        return False


def _respond(text: str):
    def fake(_req: object, timeout: object = None) -> _FakeResp:
        return _FakeResp({"response": text})

    return fake


def test_parse_extracts_array_from_surrounding_text() -> None:
    words = _parse_words(_GOOD_JSON)
    assert [w.tamil for w in words] == ["நான்", "புத்தகம்", "படிக்கிறேன்"]
    assert words[1].pos == "noun"
    assert words[1].emoji == "📖"


def test_parse_normalizes_unknown_pos_and_lowercases() -> None:
    words = _parse_words(_GOOD_JSON)
    assert words[2].pos == "verb"  # "VERB" -> lowercased + valid


def test_parse_drops_garbage_emoji() -> None:
    raw = '[{"tamil":"வீடு","pos":"noun","gloss":"house","emoji":"a house"}]'
    assert _parse_words(raw)[0].emoji == ""  # multi-char/letters rejected


def test_parse_invalid_pos_becomes_other() -> None:
    raw = '[{"tamil":"x","pos":"sparkle","gloss":"y","emoji":""}]'
    assert _parse_words(raw)[0].pos == "other"


def test_parse_returns_empty_on_non_json() -> None:
    assert _parse_words("no json here") == []
    assert _parse_words("[not valid json}") == []


def test_analyze_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond(_GOOD_JSON))
    res = analyze("நான் புத்தகம் படிக்கிறேன்")
    assert isinstance(res, SentenceAnalysis)
    assert len(res.words) == 3
    assert res.words[0].gloss == "I"


def test_analyze_blank_input_returns_empty() -> None:
    res = OllamaAnalyzer().analyze("   ")
    assert res.words == []


def test_analyze_raises_on_unparseable_model_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond("sorry, I cannot"))
    with pytest.raises(GrammarError, match="no parseable"):
        OllamaAnalyzer().analyze("நான்")


def test_analyze_raises_when_ollama_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(_req: object, timeout: object = None) -> _FakeResp:
        raise urllib.error.URLError("refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(GrammarError, match="unreachable"):
        OllamaAnalyzer().analyze("நான்")


def test_unknown_backend_raises() -> None:
    with pytest.raises(ValueError, match="Unknown grammar backend"):
        analyze("நான்", backend="nope")
