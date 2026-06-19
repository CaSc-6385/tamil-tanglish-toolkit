"""Sarvam-Translate backend — free, local, Indic-specialised translation via Ollama.

``sarvamai/sarvam-translate`` is an open-weights Indic translation model (Gemma3-4B
base, 22 Indian languages incl. Tamil). It is purpose-built for translation and
expects a SIMPLE, direct instruction — the few-shot OllamaTransliterator prompt
confuses it (it echoes the example), so this backend overrides the prompt with a
minimal one. Everything else (HTTP call, cleaning, per-word alignment) is inherited.

Pull the GGUF once:
    ollama pull hf.co/mradermacher/sarvam-translate-i1-GGUF:Q4_K_M
"""

from __future__ import annotations

import os

from tamil_edu_transliterate.ollama import OllamaTransliterator

_DEFAULT_SARVAM_MODEL = (
    os.environ.get("SARVAM_MODEL", "").strip()
    or "hf.co/mradermacher/sarvam-translate-i1-GGUF:Q4_K_M"
)


class SarvamTransliterator(OllamaTransliterator):
    """Tanglish → Tamil via the Sarvam-Translate model on Ollama."""

    name = "sarvam"

    def __init__(self, *, model: str | None = None, **kwargs: object) -> None:
        super().__init__(model=model or _DEFAULT_SARVAM_MODEL, **kwargs)  # type: ignore[arg-type]

    def _prompt(self, text: str) -> str:
        return (
            "Translate this Tanglish (Tamil written in English letters) into Tamil "
            "script. Keep real English words and punctuation as they are. "
            "Output only the Tamil line, nothing else:\n"
            f"{text}"
        )
