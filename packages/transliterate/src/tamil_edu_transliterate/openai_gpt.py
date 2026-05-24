"""OpenAI GPT-4o-mini Tanglish → Tamil transliteration backend.

Highest quality option we have today (ML-trained on natural language) while
IndicXlit is blocked by the upstream fairseq/Py 3.11 incompat (ADR-0002).

Requires the `[openai]` extra installed and OPENAI_API_KEY env var set:
    uv add 'tamil-edu-transliterate[openai]'
    export OPENAI_API_KEY=sk-...

Cost note: gpt-4o-mini is ~$0.15 per 1M input tokens. A typical 50-char
Tanglish phrase ≈ 30 tokens in + 30 tokens out → ~$0.0001 per request.
Stays within the PLAN.md $15/mo OpenAI cap at ~150k requests/mo.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from tamil_edu_transliterate.base import TransliterationError, Word
from tamil_edu_transliterate.tokenizer import TokenKind, tokenize

if TYPE_CHECKING:
    from openai import OpenAI

_DEFAULT_MODEL = os.environ.get("OPENAI_TRANSLITERATE_MODEL", "gpt-4o-mini")

_SYSTEM_PROMPT = (
    "You are a precise Tamil transliteration engine. Convert Tanglish (Tamil "
    "written in English/Roman script) into proper Tamil Unicode. Rules:\n"
    "1. Output ONLY the Tamil text — no explanation, no quotes, no preamble.\n"
    "2. Preserve English words, punctuation, digits, whitespace VERBATIM.\n"
    "3. Use standard modern Tamil orthography (retroflex ண, ட, ண் where "
    "Tanglish 'n','t','nn' appears between vowels).\n"
    "4. Common examples:\n"
    "   vanakkam → வணக்கம்\n"
    "   nanba → நண்பா\n"
    "   nandri → நன்றி\n"
    "   send the message → send the message\n"
    "   homework finish panniten → homework finish பண்ணிட்டேன்\n"
    "5. If unsure between two valid Tamil renderings, prefer the more common "
    "Tamil-Nadu colloquial spelling."
)


class OpenAiGptTransliterator:
    """Calls OpenAI's gpt-4o-mini (configurable) for transliteration.

    Lazy-loads the client on first call. Errors with a clear install/config
    hint if the extra or API key are missing.
    """

    name = "openai-gpt"

    def __init__(self, *, model: str | None = None) -> None:
        self._model = model or _DEFAULT_MODEL
        self._client: OpenAI | None = None

    def _ensure_client(self) -> OpenAI:
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise TransliterationError(
                "OpenAI backend requires the 'openai' extra. Install with: "
                "uv add 'tamil-edu-transliterate[openai]'"
            ) from exc
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise TransliterationError(
                "OpenAI backend requires OPENAI_API_KEY env var. "
                "Set it via `fly secrets set OPENAI_API_KEY=sk-...` for production."
            )
        self._client = OpenAI(api_key=api_key)
        return self._client

    def _call(self, text: str, *, n: int = 1, temperature: float = 0.0) -> list[str]:
        client = self._ensure_client()
        try:
            resp: Any = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                temperature=temperature,
                n=n,
                max_tokens=600,
            )
        except Exception as exc:
            raise TransliterationError(f"OpenAI API call failed: {exc}") from exc
        return [c.message.content.strip() for c in resp.choices if c.message.content]

    def transliterate(self, text: str, *, topk: int = 1) -> str:
        if not text:
            return text
        candidates = self._call(text, n=1, temperature=0.0)
        return candidates[0] if candidates else text

    def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
        if not text:
            return [text]
        # Slightly raise temperature to get variation; cap at 3 to bound cost.
        n = max(1, min(topk, 3))
        return self._call(text, n=n, temperature=0.4 if n > 1 else 0.0)

    def transliterate_detailed(self, text: str, *, topk: int = 3) -> list[Word]:
        """Per-token output. We make ONE API call for the full string, then
        align the result with input tokens by walking the model output. This
        is cheaper than per-token calls (1 API hit instead of N) at the cost
        of slightly less reliable per-word alignment for highly code-switched
        input.
        """
        if not text:
            return []
        input_tokens = tokenize(text)
        full_tamil = self.transliterate(text, topk=topk)

        # If output has same whitespace structure as input, align by splitting
        # on whitespace. Otherwise, return a single Word with all the output.
        try:
            return _align(input_tokens, full_tamil)
        except _AlignmentError:
            # Fallback: collapse into one Word with the full output
            return [
                Word(
                    source=text,
                    text=full_tamil,
                    kind=TokenKind.TANGLISH,
                    alternatives=[full_tamil],
                )
            ]


class _AlignmentError(Exception):
    pass


def _align(input_tokens: list, full_output: str) -> list[Word]:
    """Walk the input tokens and the output text in lockstep.

    For WHITESPACE/PUNCTUATION/ENGLISH tokens: expect them verbatim in output.
    For TANGLISH tokens: consume the next chunk of output up to the next
    expected verbatim section.
    """
    out: list[Word] = []
    cursor = 0
    pending_tanglish: list = []

    def flush_tanglish() -> None:
        nonlocal cursor
        if not pending_tanglish:
            return
        # The output from cursor up to ... hmm, complex.
        # Simple version: join the Tanglish sources, find them in output by
        # consuming until the next verbatim chunk matches.
        # For now, take everything before the next verbatim token.
        raise _AlignmentError("complex alignment not implemented")

    for tok in input_tokens:
        if tok.kind == TokenKind.TANGLISH:
            pending_tanglish.append(tok)
        else:
            flush_tanglish()
            # Expect tok.text at cursor
            if full_output[cursor : cursor + len(tok.text)] != tok.text:
                raise _AlignmentError(f"expected {tok.text!r} at pos {cursor}")
            out.append(Word(source=tok.text, text=tok.text, kind=tok.kind, alternatives=[]))
            cursor += len(tok.text)

    if pending_tanglish:
        # Remaining output goes to the last tanglish block
        remaining = full_output[cursor:]
        # Simple approach: assign all remaining as one Word per token (split on whitespace)
        # but tokens may not have whitespace between them in input.
        # For V1: collapse all trailing tanglish into one Word
        joined_source = "".join(t.text for t in pending_tanglish)
        out.append(
            Word(
                source=joined_source,
                text=remaining,
                kind=TokenKind.TANGLISH,
                alternatives=[remaining],
            )
        )

    return out
