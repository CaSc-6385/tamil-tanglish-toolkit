# tamil-edu-transliterate

Tanglish (Roman-script Tamil) → Tamil Unicode transliteration. Pluggable backends behind a single `Transliterator` protocol.

## Backends

| Backend   | Class                     | Deps                                     | Quality         | Speed                   | Notes                                                                    |
| --------- | ------------------------- | ---------------------------------------- | --------------- | ----------------------- | ------------------------------------------------------------------------ |
| Baseline  | `BaselineTransliterator`  | none                                     | none (identity) | instant                 | Passthrough — used as the eval baseline and as a fast stand-in for tests |
| IndicXlit | `IndicXlitTransliterator` | `ai4bharat-transliteration` (~1GB model) | SOTA open       | ~50–200ms / word on CPU | Wraps `ai4bharat.transliteration.XlitEngine`                             |

More backends planned: rule-based (Aksharamukha), classifier-routed, Tamil-LLaMA prompted.

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
