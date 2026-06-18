# tamil-edu-transliterate

Tanglish (Roman-script Tamil) → Tamil Unicode transliteration. Pluggable backends behind a single `Transliterator` protocol.

## Backends

| Backend      | Class                        | Deps                                     | Quality         | Speed                   | Notes                                                                       |
| ------------ | ---------------------------- | ---------------------------------------- | --------------- | ----------------------- | --------------------------------------------------------------------------- |
| Baseline     | `BaselineTransliterator`     | none                                     | none (identity) | instant                 | Passthrough — used as the eval baseline and as a fast stand-in for tests    |
| Ollama       | `OllamaTransliterator`       | none (uses a local Ollama server)        | high, **free**  | ~5s / phrase on GPU     | Open Tamil model via Ollama (default `gemma2:9b`). No API key. **Default.** |
| Aksharamukha | `AksharamukhaTransliterator` | `aksharamukha`                           | rule-based      | instant                 | Offline rule-based fallback                                                 |
| OpenAI       | `OpenAiGptTransliterator`    | `openai` + `OPENAI_API_KEY`              | high (paid)     | network                 | GPT-4o-mini; paid                                                           |
| IndicXlit    | `IndicXlitTransliterator`    | `ai4bharat-transliteration` (~1GB model) | SOTA open       | ~50–200ms / word on CPU | Wraps `ai4bharat.transliteration.XlitEngine` — blocked (ADR-0002)           |

### Ollama backend (free, local — default)

```bash
ollama pull gemma2:9b            # open Tamil-capable model (or chandralabs/tamil-llama)
export TRANSLITERATE_BACKEND=ollama
```

Config via env: `OLLAMA_MODEL` (default `gemma2:9b`), `OLLAMA_API_URL`
(default `http://127.0.0.1:11434/api/generate`), `OLLAMA_TIMEOUT_S` (default `120`).
The instruction + few-shot examples are embedded in the prompt with a stop
sequence, so the model returns exactly one transliterated line and preserves
code-switched English verbatim (`send the message reply pannu` →
`send the message reply பண்ணு`).

## Install

```bash
# core only (baseline)
uv add tamil-edu-transliterate

# with IndicXlit ML backend
uv add 'tamil-edu-transliterate[indicxlit]'
```

## Usage

```python
from tamil_edu_transliterate import transliterate

# default: baseline (passthrough) — fast, no deps
transliterate("vanakkam")
# 'vanakkam'

# IndicXlit (requires the `indicxlit` extra installed)
transliterate("vanakkam", backend="indicxlit")
# 'வணக்கம்'
```

Or pick the backend explicitly:

```python
from tamil_edu_transliterate import BaselineTransliterator, IndicXlitTransliterator

t = IndicXlitTransliterator()  # lazy-loads model on first call
t.transliterate("vanakkam nanba")
# 'வணக்கம் நண்பா'
```

## Protocol

Implement `Transliterator` to add a new backend:

```python
from tamil_edu_transliterate import Transliterator

class MyBackend:
    name = "mine"
    def transliterate(self, text: str, *, topk: int = 1) -> str: ...
    def alternatives(self, text: str, *, topk: int = 3) -> list[str]: ...
```

## Roadmap (per docs/SPRINTS.md)

| Sprint | Story                                                   | Status                                                                             |
| ------ | ------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| S1-1   | IndicXlit Tamil model wrapper                           | **in progress** — scaffold + skeleton landed; full model integration tests pending |
| S1-2   | Code-switch handling (preserve English tokens verbatim) | pending                                                                            |
| S1-5   | Per-word confidence + alternatives                      | pending — Transliterator.alternatives() ready                                      |
