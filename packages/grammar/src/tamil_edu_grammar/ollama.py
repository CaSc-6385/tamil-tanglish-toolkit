"""Grammar / sentence-structure analyzer backed by a local Ollama model.

Given a Tamil sentence, it returns a per-word breakdown: part of speech, a short
English gloss, and a picture emoji for concrete words. It runs a single
JSON-producing call against a general instruction model (default gemma2:9b, which
follows structured-output instructions reliably). Free, local, no API key.

Config via env (all optional):
    GRAMMAR_MODEL      model tag         (default: gemma2:9b)
    OLLAMA_API_URL     generate endpoint (default: http://127.0.0.1:11434/api/generate)
    GRAMMAR_TIMEOUT_S  request timeout   (default: 120)
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from tamil_edu_grammar.base import POS_TAGS, GrammarError, SentenceAnalysis, WordAnalysis


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


_DEFAULT_MODEL = os.environ.get("GRAMMAR_MODEL", "gemma2:9b").strip() or "gemma2:9b"
_DEFAULT_URL = os.environ.get("OLLAMA_API_URL", "").strip() or "http://127.0.0.1:11434/api/generate"
_DEFAULT_TIMEOUT = _int_env("GRAMMAR_TIMEOUT_S", 120)

_INSTRUCTION = (
    "You are a Tamil teacher breaking a sentence down for a young child. For EVERY "
    "word of the Tamil sentence, output an object with these fields:\n"
    '  "tamil": the word exactly as written,\n'
    '  "pos": one of noun, verb, adjective, adverb, pronoun, postposition, '
    "conjunction, numeral, particle, other,\n"
    '  "gloss": a 1-2 word English meaning,\n'
    '  "emoji": ONE emoji that pictures the word if it is a concrete object, animal, '
    "person, place or action; otherwise an empty string.\n"
    "Output ONLY a JSON array of these objects, in sentence order, nothing else."
)
_FEWSHOT = (
    "Sentence: நான் பெரிய புத்தகம் படிக்கிறேன்\n"
    "JSON: ["
    '{"tamil":"நான்","pos":"pronoun","gloss":"I","emoji":"🙋"},'
    '{"tamil":"பெரிய","pos":"adjective","gloss":"big","emoji":""},'
    '{"tamil":"புத்தகம்","pos":"noun","gloss":"book","emoji":"📖"},'
    '{"tamil":"படிக்கிறேன்","pos":"verb","gloss":"read","emoji":"📚"}]\n'
)


def _build_prompt(text: str) -> str:
    return f"{_INSTRUCTION}\n\n{_FEWSHOT}\nSentence: {text}\nJSON:"


class OllamaAnalyzer:
    """Per-word grammar analysis via a local Ollama model."""

    name = "ollama"

    def __init__(self, *, model: str | None = None, url: str | None = None) -> None:
        self._model = model or _DEFAULT_MODEL
        self._url = url or _DEFAULT_URL

    def _generate(self, text: str) -> str:
        payload = {
            "model": self._model,
            "prompt": _build_prompt(text),
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 700},
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise GrammarError(
                f"Ollama unreachable at {self._url}. Start Ollama and pull the model "
                f"({self._model})."
            ) from exc
        except Exception as exc:
            raise GrammarError(f"Ollama request failed: {exc}") from exc
        return str(data.get("response", ""))

    def analyze(self, text: str) -> SentenceAnalysis:
        if not text.strip():
            return SentenceAnalysis(tamil=text, words=[], model=self._model)
        raw = self._generate(text)
        words = _parse_words(raw)
        if not words:
            raise GrammarError("Model returned no parseable word analysis.")
        return SentenceAnalysis(tamil=text, words=words, model=self._model)


def _parse_words(raw: str) -> list[WordAnalysis]:
    """Extract the JSON array from the model output and validate each entry."""
    start = raw.find("[")
    end = raw.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []

    words: list[WordAnalysis] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        tamil = str(item.get("tamil", "")).strip()
        if not tamil:
            continue
        pos = str(item.get("pos", "other")).strip().lower()
        if pos not in POS_TAGS:
            pos = "other"
        gloss = str(item.get("gloss", "")).strip()
        emoji = str(item.get("emoji", "")).strip()
        # Guard against the model stuffing words/sentences into the emoji field.
        if len(emoji) > 4 or re.search(r"[A-Za-z஀-௿]", emoji):
            emoji = ""
        words.append(WordAnalysis(tamil=tamil, pos=pos, gloss=gloss, emoji=emoji))
    return words
