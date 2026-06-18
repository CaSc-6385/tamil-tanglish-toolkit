"""Tests for the free local Ollama transliteration backend.

No running Ollama is needed: ``urllib.request.urlopen`` is monkeypatched so the
request building, response parsing, word alignment, and error handling are all
covered deterministically.
"""

from __future__ import annotations

import json
import urllib.error

import pytest
from tamil_edu_transliterate import TransliterationError
from tamil_edu_transliterate.ollama import OllamaTransliterator
from tamil_edu_transliterate.tokenizer import TokenKind


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


def test_transliterate_returns_model_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond("வணக்கம் நண்பா"))
    assert OllamaTransliterator().transliterate("vanakkam nanba") == "வணக்கம் நண்பா"


def test_blank_input_skips_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    def fake(_req: object, timeout: object = None) -> _FakeResp:
        calls["n"] += 1
        return _FakeResp({"response": "x"})

    monkeypatch.setattr("urllib.request.urlopen", fake)
    t = OllamaTransliterator()
    assert t.transliterate("") == ""
    assert t.transliterate("   ") == "   "
    assert calls["n"] == 0


def test_clean_strips_quotes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond('"வணக்கம்"'))
    assert OllamaTransliterator().transliterate("vanakkam") == "வணக்கம்"


def test_detailed_aligns_word_for_word(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond("வணக்கம் நண்பா"))
    words = OllamaTransliterator().transliterate_detailed("vanakkam nanba")
    assert "".join(w.text for w in words) == "வணக்கம் நண்பா"  # round-trip holds
    non_ws = [w.text for w in words if w.kind != TokenKind.WHITESPACE]
    assert non_ws == ["வணக்கம்", "நண்பா"]


def test_detailed_preserves_english_token_kind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond("send வணக்கம்"))
    words = OllamaTransliterator().transliterate_detailed("send vanakkam")
    by_source = {w.source: w.kind for w in words if w.kind != TokenKind.WHITESPACE}
    assert by_source["send"] == TokenKind.ENGLISH
    assert by_source["vanakkam"] == TokenKind.TANGLISH


def test_detailed_falls_back_to_single_word_on_count_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond("வணக்கம் நல்ல நண்பா"))
    words = OllamaTransliterator().transliterate_detailed("vanakkam nanba")
    assert len(words) == 1
    assert words[0].text == "வணக்கம் நல்ல நண்பா"


def test_detailed_empty_input() -> None:
    assert OllamaTransliterator().transliterate_detailed("") == []


def test_alternatives_dedupes_identical_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("urllib.request.urlopen", _respond("வணக்கம்"))
    assert OllamaTransliterator().alternatives("vanakkam", topk=3) == ["வணக்கம்"]


def test_unreachable_server_raises_transliteration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(_req: object, timeout: object = None) -> _FakeResp:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(TransliterationError, match="unreachable"):
        OllamaTransliterator().transliterate("vanakkam")


def test_malformed_response_raises_transliteration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BadResp:
        def read(self) -> bytes:
            return b"not json"

        def __enter__(self) -> _BadResp:
            return self

        def __exit__(self, *_a: object) -> bool:
            return False

    monkeypatch.setattr("urllib.request.urlopen", lambda _req, timeout=None: _BadResp())
    with pytest.raises(TransliterationError):
        OllamaTransliterator().transliterate("vanakkam")
