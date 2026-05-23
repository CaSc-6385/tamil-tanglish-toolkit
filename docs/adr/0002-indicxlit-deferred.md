# ADR-0002 — IndicXlit deferred; aksharamukha for real-model eval until unblocked

- **Status**: Accepted
- **Date**: 2026-05-23
- **Deciders**: schandra@ieee.org
- **Supersedes**: n/a (extends ADR-0001 and S1-1 plan in docs/SPRINTS.md)
- **Related**: PLAN.md §6 (tech stack), SPRINTS.md S1-1 + S1-7

## Context

PLAN.md v3 §6 picks `ai4bharat/IndicXlit` (Tamil) as the primary transliteration model and S1-1 acceptance is "CER ≤ 15% on golden v1." We attempted to install and run IndicXlit during Sprint 1 to verify CER and unblock S1-7 (baseline report).

Three install attempts:

| Env | Python | Result |
|---|---|---|
| Windows local | 3.13 | `ai4bharat-transliteration` install fails: `fairseq` (transitive dep) has no Python 3.13 wheel and its source build references `fairseq/version.txt` which doesn't ship in the sdist. |
| Linux CI | 3.11 | Install succeeds; runtime fails at `XlitEngine()` construction: `fairseq.dataclass.configs` uses `dataclass` with mutable defaults, which raises `ValueError: mutable default ... for field common is not allowed: use default_factory` on Python ≥ 3.11. |
| Linux CI | 3.10 | Our pyproject requires `python>=3.11` (we use `StrEnum` in `tokenizer.py`); `uv sync` refuses Python 3.10. Lowering would mean dropping modern features across the codebase. |

Net: **IndicXlit is genuinely unrunnable in our environment today.** It needs Python ≤ 3.10 (fairseq bug), and our code needs Python ≥ 3.11 (StrEnum + other typing niceties). The conflict is at the upstream level — not fixable on our side without major investment.

## Decision

1. **Keep `IndicXlitTransliterator` in the library** unchanged. It's correctly written; whenever upstream unblocks (fairseq fix, or a fairseq-free fork), it'll just work. Tests pass via mocked engine.

2. **Use `aksharamukha`** as the working "real-model" backend for eval and the localhost demo until IndicXlit is unblocked. Aksharamukha is pure Python, rule-based, no torch/fairseq deps, works on every Python version we'll ever target. Quality is meaningfully lower (CER ~35% vs. expected ~10% for IndicXlit), but it produces real Tamil output and proves the pipeline end-to-end.

3. **Defer S1-1 acceptance gate (CER ≤ 15%)** to the sprint when IndicXlit is unblocked. Track aksharamukha numbers as the floor we'll improve from, not as the V1 target.

4. **Re-evaluate quarterly**: check whether (a) fairseq has been fixed, (b) a fairseq-free IndicXlit fork has appeared, or (c) a hosted IndicXlit endpoint at acceptable cost exists. If yes → switch back. If no after 2026 Q4 → consider replacing IndicXlit in PLAN.md with another ML transliterator (e.g. Helsinki-NLP/opus-mt-en-mul or a Tamil-LLaMA prompt).

## Consequences

### Positive

- **Unblocks shipping**: localhost demo, eval CI workflow, eval report generation all work today via aksharamukha.
- **Zero cost increase**: aksharamukha is open-source, pure Python, no model download, no GPU.
- **Honest about quality**: 35% CER is published, not hidden. Users see what they're getting.
- **Easy path back**: when fairseq is unblocked, flipping the default backend from `aksharamukha` to `indicxlit` is a one-line change.

### Negative

- **CER is well above target**: the kid-friendly UX promise of "type Tanglish, get Tamil" is degraded — characters like `nandri` come out as `நந்த்³ரி` (Sanskrit-style numerals on aspirated consonants) instead of `நன்றி`. Adult Tamil speakers will notice immediately. We mitigate by clearly labeling the backend in the response (`backend: "aksharamukha"`) and the homepage footer.
- **Backend story is now 3-way** (baseline / aksharamukha / indicxlit), which complicates docs and onboarding.
- **Sprint 1 exit gate slips**: S1-1 acceptance criterion is officially not met. Sprint retro should note this and re-plan S1-7 readiness for a later sprint.

### Reconsider when

- A fairseq release fixes the Py 3.11+ dataclass issue (track [fairseq #5012](https://github.com/facebookresearch/fairseq/issues) or successor)
- ai4bharat ships IndicXlit as a fairseq-free package (it's been requested upstream)
- A hosted IndicXlit API surfaces at < $20/mo for our expected request volume
- We choose to host a Python 3.10 worker just for transliteration (would cost ~$5/mo extra on Hetzner; within budget but adds ops surface)

## Alternatives considered

| Option | Why not (now) |
|---|---|
| Drop Python floor to 3.10 to use fairseq | Loses StrEnum + other typing features across the codebase; technical debt for one Sprint 1 story |
| Patch fairseq locally | Maintaining a fork of a 200k-line ML framework is not in scope for an education-toolkit project |
| Use a different ML transliterator (Helsinki-NLP/opus-mt) | Quality unknown for Tamil; another ~1GB model download; same ops cost. Worth a future spike. |
| Use Tamil-LLaMA via Ollama as the transliterator (not just corrector) | Overkill (7B model for a tokenization task) and slow (~200ms/word); breaks PLAN.md's "IndicXlit transliterates, Tamil-LLaMA corrects" architecture |
| Skip real-model eval entirely | Cleaner but leaves no measurement story; user gets baseline-only numbers and no way to track real-model regressions |
