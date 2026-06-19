"""Contract tests for POST /analyze (Sarvam translate + gemma2 breakdown pipeline).

The two model calls are monkeypatched, so no running Ollama is needed.
"""

from __future__ import annotations

import pytest
import tamil_edu_api.main as main
from fastapi.testclient import TestClient
from tamil_edu_api.main import app
from tamil_edu_grammar import SentenceAnalysis, WordAnalysis


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class _FakeTranslator:
    _model = "sarvam-test"

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        return "வணக்கம் நண்பா"


def _patch_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "_get", lambda _backend: _FakeTranslator())
    monkeypatch.setattr(
        main,
        "analyze_grammar",
        lambda _tamil: SentenceAnalysis(
            tamil="வணக்கம் நண்பா",
            words=[
                WordAnalysis(tamil="வணக்கம்", pos="noun", gloss="hello", emoji="🙏"),
                WordAnalysis(tamil="நண்பா", pos="noun", gloss="friend", emoji="🧑"),
            ],
            model="gemma2-test",
        ),
    )


def test_analyze_returns_translation_and_breakdown(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_pipeline(monkeypatch)
    body = client.post("/analyze", json={"text": "vanakkam nanba"}).json()
    assert body["tamil"] == "வணக்கம் நண்பா"
    assert body["translate_model"] == "sarvam-test"
    assert body["analyze_model"] == "gemma2-test"
    assert [w["pos"] for w in body["words"]] == ["noun", "noun"]
    assert body["words"][0]["emoji"] == "🙏"
    assert body["words"][1]["gloss"] == "friend"
    assert isinstance(body["duration_ms"], int)


def test_analyze_degrades_gracefully_when_breakdown_fails(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tamil_edu_grammar import GrammarError

    monkeypatch.setattr(main, "_get", lambda _backend: _FakeTranslator())

    def boom(_tamil: str) -> SentenceAnalysis:
        raise GrammarError("model down")

    monkeypatch.setattr(main, "analyze_grammar", boom)
    r = client.post("/analyze", json={"text": "vanakkam nanba"})
    assert r.status_code == 200
    body = r.json()
    assert body["tamil"] == "வணக்கம் நண்பா"  # translation still returned
    assert body["words"] == []  # breakdown empty, no 500


def test_analyze_translation_failure_returns_503(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tamil_edu_transliterate import TransliterationError

    class _BoomTranslator:
        _model = "sarvam-test"

        def transliterate(self, text: str, *, topk: int = 1) -> str:
            raise TransliterationError("ollama unreachable")

    monkeypatch.setattr(main, "_get", lambda _backend: _BoomTranslator())
    r = client.post("/analyze", json={"text": "vanakkam nanba"})
    assert r.status_code == 503


def test_analyze_rejects_oversized_text(client: TestClient) -> None:
    r = client.post("/analyze", json={"text": "x" * 2001})
    assert r.status_code == 422
