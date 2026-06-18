"""Ollama Tanglish → Tamil transliteration backend — free, local, open-source.

Uses a Tamil-capable open model served by a local (or self-hosted) Ollama instance.
No API key, no per-request cost — the model runs on the Ollama box (PLAN.md: a
Hetzner CX32) or on any machine with Ollama. This is the free alternative to the
paid OpenAI backend and the rule-based aksharamukha substitute.

Pull a model once, then select this backend:

    ollama pull gemma2:9b          # strong Tamil, open weights (default)
    # or a Tamil-specialised model, e.g. chandralabs/tamil-llama via Ollama
    export TRANSLITERATE_BACKEND=ollama

Config via env (all optional):
    OLLAMA_MODEL        model tag        (default: gemma2:9b)
    OLLAMA_API_URL      generate endpoint(default: http://127.0.0.1:11434/api/generate)
    OLLAMA_TIMEOUT_S    request timeout  (default: 120)
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from tamil_edu_transliterate.base import TransliterationError, Word
from tamil_edu_transliterate.tokenizer import TokenKind, tokenize


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


_DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2:9b").strip() or "gemma2:9b"
_DEFAULT_URL = os.environ.get("OLLAMA_API_URL", "").strip() or "http://127.0.0.1:11434/api/generate"
_DEFAULT_TIMEOUT = _int_env("OLLAMA_TIMEOUT_S", 120)

# The instruction + few-shot examples must live in the PROMPT (not a `system`
# field): general chat models like gemma2 follow the system role unreliably over
# /api/generate and otherwise just echo the input or answer conversationally.
# The trailing "Tamil:" cue + a stop sequence make the model emit exactly one line.
_INSTRUCTION = (
    "Transliterate the Tanglish (Tamil written in English letters) on the last line "
    "into Tamil Unicode script. Keep real English words, numbers, punctuation and "
    "spacing exactly as written. Reply with ONLY the Tamil line — no quotes, no notes."
)
_FEWSHOT = (
    "Tanglish: vanakkam nanba\nTamil: வணக்கம் நண்பா\n"
    "Tanglish: naan inniki tamil padikiren\nTamil: நான் இன்னிக்கி தமிழ் படிக்கிறேன்\n"
    "Tanglish: send the message reply pannu\nTamil: send the message reply பண்ணு\n"
    "Tanglish: enaku romba pasikuthu\nTamil: எனக்கு ரொம்ப பசிக்குது\n"
)


def _build_prompt(text: str) -> str:
    return f"{_INSTRUCTION}\n\n{_FEWSHOT}Tanglish: {text}\nTamil:"


class OllamaTransliterator:
    """Transliterate via a local Ollama model (free, no API key).

    Cheap to construct — the model loads inside Ollama on first request, not here.
    """

    name = "ollama"

    def __init__(
        self,
        *,
        model: str | None = None,
        url: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._model = model or _DEFAULT_MODEL
        self._url = url or _DEFAULT_URL
        self._timeout = timeout or _DEFAULT_TIMEOUT

    def _generate(self, text: str, *, temperature: float) -> str:
        payload = {
            "model": self._model,
            "prompt": _build_prompt(text),
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 256,
                # Stop as soon as the model would start another example / new line block.
                "stop": ["\nTanglish:", "\nTamil:", "\n\n"],
            },
        }
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise TransliterationError(
                f"Ollama unreachable at {self._url}. Start Ollama and pull the model "
                f"({self._model})."
            ) from exc
        except Exception as exc:  # malformed response, timeout, etc.
            raise TransliterationError(f"Ollama request failed: {exc}") from exc
        return _clean(str(data.get("response", "")))

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        if not text.strip():
            return text
        out = self._generate(text, temperature=0.0)
        return out or text

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        if not text.strip():
            return [text]
        # First candidate is deterministic; extras add a little temperature for
        # variety. Bounded to keep latency sane on a CPU box.
        n = max(1, min(topk, 3))
        seen: list[str] = []
        for i in range(n):
            cand = self._generate(text, temperature=0.0 if i == 0 else 0.5)
            if cand and cand not in seen:
                seen.append(cand)
        return seen or [self.transliterate(text)]

    def transliterate_detailed(self, text: str, *, topk: int = 3) -> list[Word]:
        """Per-token output from a single model call.

        We transliterate the whole string once, then align word-for-word when the
        input and output have the same number of space-separated words (the common
        case for kids). Otherwise we fall back to one Word carrying the full output.
        Either way ``"".join(w.text for w in result)`` reconstructs the string.
        """
        if not text:
            return []
        tokens = tokenize(text)
        full = self.transliterate(text, topk=topk)

        out_words = full.split()
        non_ws = [t for t in tokens if t.kind != TokenKind.WHITESPACE]
        if out_words and len(out_words) == len(non_ws):
            words: list[Word] = []
            out_iter = iter(out_words)
            for tok in tokens:
                if tok.kind == TokenKind.WHITESPACE:
                    words.append(Word(source=tok.text, text=tok.text, kind=tok.kind))
                    continue
                chosen = next(out_iter)
                alts = [chosen] if tok.kind == TokenKind.TANGLISH else []
                words.append(Word(source=tok.text, text=chosen, kind=tok.kind, alternatives=alts))
            return words

        return [Word(source=text, text=full, kind=TokenKind.TANGLISH, alternatives=[full])]


def _clean(text: str) -> str:
    cleaned = text.strip()
    # Strip code fences the model may wrap output in.
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else ""
    cleaned = cleaned.removesuffix("```").strip()
    # Take the first non-empty line (the answer is a single line) and drop any
    # echoed "Tamil:" label or surrounding quotes.
    for line in cleaned.splitlines():
        line = line.strip()
        if line:
            cleaned = line
            break
    else:
        cleaned = ""
    if cleaned.lower().startswith("tamil:"):
        cleaned = cleaned[len("tamil:") :].strip()
    return cleaned.strip('"').strip("'").strip()
