# Testing Plan

Test strategy for `chandralabs/tamil-edu-toolkit`. Aligned with PLAN.md v3 (frozen) and DEVELOPMENT.md DoD.

## 1. Test pyramid

```
              /\
             /E2E\         ~5%  Playwright (web), Detox (mobile)
            /------\
           / Integ  \      ~15% pytest + httpx for FastAPI; React Testing Library
          /----------\
         / Unit       \    ~60% pytest, vitest
        /--------------\
       / ML Eval        \  ~20% jiwer (CER/WER), BLEU, native-rater rubric
      /------------------\
```

Per-PR: unit + integration + eval-smoke (10 golden pairs, fast).
Nightly: full eval-suite (1000 golden pairs + native-rater queue).
Pre-release: E2E + load + accessibility.

## 2. Frameworks

| Layer | Framework | Location |
|---|---|---|
| Python unit | `pytest` + `pytest-cov` | each `packages/<x>/tests/` |
| Python integration | `pytest-asyncio` + `httpx.AsyncClient` | `apps/api/tests/integration/` |
| TS unit | `vitest` | each `apps/<x>/__tests__/` |
| React component | `@testing-library/react` | colocated with components |
| Web E2E | `playwright` | `apps/web/e2e/` |
| Mobile E2E (S4) | `maestro` (lighter than Detox) | `apps/mobile/e2e/` |
| ML eval | custom harness `eval/run.py` using `jiwer`, `sacrebleu`, native-rater queue | `eval/` |
| Accessibility | `axe-core` via Playwright | `apps/web/e2e/a11y.spec.ts` |
| Load (pre-release) | `k6` | `infra/load/` |

## 3. Coverage gates

- **New code**: ≥ 80% line coverage (per PR). Enforced by `pytest-cov --fail-under=80` on changed files via `diff-cover`.
- **Overall**: track but don't gate (legacy coverage debt acceptable, new code can't add to it).
- **No coverage of generated code** (e.g., OpenAPI clients in `packages/sdk-ts/`).
- **Coverage report uploaded** to Codecov free tier per PR.

## 4. ML eval methodology

### 4.1 Golden eval set (1000 Tanglish→Tamil pairs)

Built in S0-4. Composition:
| Domain | Pairs | Source |
|---|---|---|
| Conversation (greetings, family, school) | 200 | Hand-curated |
| Names (people, places, brands) | 200 | Hand-curated + Wikipedia |
| School sentences (math, science) | 200 | Tamil textbook samples |
| Code-switched (Tanglish with English words) | 200 | Scraped from r/tamil, YouTube comments |
| News headlines | 200 | Tamil news sites, manually cleaned |

Each row: `id, tanglish, expected_tamil, domain, difficulty, reviewer, notes`. CSV in `data/golden/v1.csv`. Versioned — never edit; new revs = `v2.csv`.

### 4.2 Quantitative metrics

| Metric | Tool | Target (V1) |
|---|---|---|
| **CER** (Character Error Rate) | `jiwer.cer` | ≤ 12% S1; ≤ 7% S2 |
| **WER** (Word Error Rate) | `jiwer.wer` | ≤ 25% S1; ≤ 18% S2 |
| **BLEU-4** | `sacrebleu` | ≥ 60 S1; ≥ 72 S2 |
| **chrF** | `sacrebleu` | ≥ 75 S1; ≥ 82 S2 |
| **Per-domain breakdown** | custom | published in every report |

### 4.3 Qualitative: native-speaker rubric

Sprints 2+ add native-speaker rating on a 100-sample stratified slice per release:

| Score | Meaning |
|---|---|
| 5 | Perfect — would write exactly this |
| 4 | Correct but stylistically odd |
| 3 | Comprehensible but has minor errors |
| 2 | Significant errors but core meaning preserved |
| 1 | Wrong or unintelligible |

**Pre-release gate**: ≥ 80% of samples rated ≥ 4.
Raters: you + 2 reviewers (recruit via Tamil-school network). Compensate or thank-by-name.

### 4.4 Eval harness CLI

```
python eval/run.py --model baseline --set v1 --sample 100
python eval/run.py --model tamil-llama-7b --set v1   # full
python eval/run.py --compare baseline,tamil-llama-7b,gpt-4o-mini --domain conversation
```

Output: `eval/reports/YYYY-MM-DD-<model>-<set>.md` with metrics, top-N errors, cost.

## 5. Pre-merge gates (per sprint)

| Gate | S0 | S1 | S2 | S3 | S4 | S5 | S6 |
|---|---|---|---|---|---|---|---|
| Lint green | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Unit tests pass | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Coverage ≥ 80% new code | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Build green (web + api) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Integration tests | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Eval-smoke (10 pairs) | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Web E2E (Playwright) | – | – | – | ✓ | ✓ | ✓ | ✓ |
| Mobile E2E (Maestro) | – | – | – | – | ✓ | ✓ | ✓ |
| A11y axe scan | – | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Lighthouse perf ≥ 80 | – | – | ✓ | ✓ | – | ✓ | ✓ |
| Native-rater ≥ 4/5 on 80% | – | – | ✓ | ✓ | ✓ | ✓ | ✓ |
| Load test (k6, 50 RPS) | – | – | – | – | – | – | ✓ |

## 6. Sprint exit gates (release-readiness)

Run at end of each sprint before tagging:
- All PRs in milestone merged
- Nightly eval ran successfully ≥ 3 of last 5 nights
- No P0/P1 bugs open
- Cost ledger updated for the sprint
- Demo recording produced
- Retro doc written

## 7. Bug triage SLA

| Severity | Definition | Response |
|---|---|---|
| **P0** | Prod down, data loss, security incident | Immediate; drop everything |
| **P1** | Core feature broken for a major use case | Within 1 day |
| **P2** | Workaround exists, not blocking demo | Within sprint |
| **P3** | Cosmetic, edge-case, nice-to-have | Backlog |

Track via GitHub Issues with `bug` + severity label. Auto-assign P0/P1 to self.

## 8. Test data strategy

- **Golden eval set**: versioned in repo (`data/golden/v1.csv`). Treat as code.
- **Augmentation set**: separate file, never used for eval, only training/prompting examples.
- **PII**: zero. Kid audience → no real names, no real student work, no addresses, no school identifiers in any test file.
- **Synthetic Tanglish**: generated samples for stress tests OK; mark `synthetic=true` column.

## 9. Manual testing (the parts CI can't automate)

Per release:
- 5 kid-perspective walk-throughs (mascot reactions, audio, streak feel)
- Cross-browser smoke (Chrome, Safari, Firefox, Mobile Safari, Chrome Android)
- Dark mode visual diff
- Tamil text rendering on iOS/Android (font glyph completeness)
- COPPA review checklist (no PII flow, no third-party trackers without consent banner)

Checklist lives in `docs/release-checklist.md` (to be created in S0).

## 10. Observability for testing

- **Sentry**: every error in prod tagged with `release` and `feature`. Test errors filtered by env.
- **PostHog**: track key events: `translate.requested`, `translate.succeeded`, `correct.toggled`, `ocr.uploaded`, `streak.day`. Used to detect silent regressions (e.g., success rate drops after deploy).
- **Eval-nightly artifact**: posted to GitHub Actions summary + Slack/email if metric drops > 2pp from previous run.
