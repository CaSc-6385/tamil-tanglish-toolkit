# Tamil Education Toolkit — Master Plan (v3 FROZEN)

**Status**: Frozen 2026-05-22. Changes require new version (v4) — don't edit in place.
**Owner**: schandra@ieee.org
**Repos**: `chandralabs/tamil-edu-toolkit` (new, this project) + existing AOST site repo (TBD location)
**Hackathon context**: For Students track — topic: "Tanglish to Tamil Translator"

---

## 1. Vision

A kid-friendly tool that converts **Tanglish** (Tamil written in Roman script — "vanakkam nanba") into correct **Tamil Unicode** (`வணக்கம் நண்பா`), with a grammar-aware correction layer and a stretch path for printed-text OCR. Web first, iOS second, integrated under the Academy of Smart Thinkers (AOST) brand at `tamil.academyofsmartthinkers.com`.

**Why this topic** (from the five hackathon options): Tanglish→Tamil has the lowest tech risk, highest user pain (every Tamil-learning kid and diaspora family hits this), reuses existing Tamil-LLaMA work, and has no head-on competitor for the kid-education audience (Vāṇi targets adult journalists).

## 2. Positioning vs. Vāṇi (vaanieditor.com)

|              | **Vāṇi**                         | **Us (AOST Tamil)**                           |
| ------------ | -------------------------------- | --------------------------------------------- |
| Direction    | Tamil-in → Tamil-out (proofread) | **Tanglish/image-in → Tamil-out (produce)**   |
| Audience     | Journalists, authors, publishers | **Kids 8–13, parents, Tamil-school teachers** |
| UX           | Dense editor                     | **Playful, mascot, audio, gamified**          |
| Pricing      | ₹100/mo Pro                      | **Free for students; school license later**   |
| Distribution | Web, Chrome ext, RapidAPI, PyPI  | Web → iOS → Chrome ext → PyPI                 |

**Strategic call**: Vāṇi and AOST Tamil are complementary, not competitive. AOST Tamil can export to Vāṇi's API as a downstream proofreading step for advanced users.

## 3. Scope (MoSCoW)

| Priority       | Item                                                                                                                                                              |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Must**       | Typed Tanglish → Tamil Unicode · web UI (kid-friendly) · grammar-correction toggle · ≥ 1000-pair golden eval set · public API · iOS app · AOST subdomain live     |
| **Should**     | Per-word confidence + alternatives · copy/download · Tamil text-to-speech for output · streaks/badges · word-of-the-day · parent/teacher view · printed-image OCR |
| **Could**      | Chrome extension · Python PyPI SDK · RapidAPI listing · Tamil number tutor · custom Tanglish keyboard (iOS extension)                                             |
| **Won't (V1)** | Handwriting OCR · Android Play Store (later) · dialect selector · offline grammar correction · Vāṇi-style 130M-word lexicon                                       |

## 4. Users & success metrics

| User                      | Need                                                   | Metric                                                      |
| ------------------------- | ------------------------------------------------------ | ----------------------------------------------------------- |
| Tamil-learning kid (8–13) | Type Tanglish, get correct Tamil for homework/messages | ≥ 90% character accuracy on top-1000 common words           |
| Parent                    | See child's practice; trust the output                 | Parent view shows last 30 days; ≥ 4/5 native-speaker rating |
| Tamil-school teacher      | Bulk-convert printed worksheets                        | Printed-image OCR F1 ≥ 0.85                                 |

## 5. Architecture

```
┌──────────────┐       ┌─────────────┐
│  Next.js UI  │       │  Expo iOS   │
│ (kid-themed) │       │  (Sprint 4) │
└──────┬───────┘       └──────┬──────┘
       │ POST /translate      │ same API
       └──────────┬───────────┘
                  ▼
         ┌──────────────────┐
         │  FastAPI         │
         │  (Fly.io free)   │
         └────────┬─────────┘
                  │
   ┌──────────────┼──────────────────┬──────────────┐
   ▼              ▼                  ▼              ▼
┌─────────┐ ┌──────────────┐  ┌─────────────┐ ┌──────────┐
│IndicXlit│ │Tamil-LLaMA   │  │GPT-4o-mini  │ │TrOCR/    │
│transla- │ │Q4 GGUF via   │  │FALLBACK     │ │Paddle    │
│tion     │ │Ollama on     │  │(latency>3s  │ │(OCR S3)  │
│(CPU)    │ │Hetzner CX32  │  │or queue>5)  │ │          │
└─────────┘ └──────────────┘  └─────────────┘ └──────────┘
                  │
                  ▼
         ┌────────────────────┐
         │ Postgres (Supabase)│
         │ + S3 (Cloudflare R2)│
         │ + PostHog telemetry │
         └────────────────────┘
```

**Cost-driven architecture decisions:**

- Primary corrector: **Tamil-LLaMA 7B Q4_K_M on Ollama** (CPU) — $5/mo
- Fallback corrector: **GPT-4o-mini** (only when Ollama is slow/queued) — $5-10/mo
- **No Modal GPU in V1** — saves ~$30/mo vs. earlier plan

## 6. Tech stack

| Layer            | Choice                                                         | Why                                                |
| ---------------- | -------------------------------------------------------------- | -------------------------------------------------- |
| Frontend         | Next.js 14 + Tailwind + shadcn/ui                              | Kid-friendly theming on top of mature primitives   |
| Mobile           | Expo SDK 51 (React Native)                                     | iOS first; Android free as bonus later             |
| Backend          | FastAPI + Pydantic                                             | Async, type-safe; works with HF + llama-cpp-python |
| Transliteration  | `ai4bharat/IndicXlit` Tamil                                    | SOTA open transliteration                          |
| Grammar          | `chandralabs/tamil-llama` 7B Q4_K_M via Ollama                 | Self-host, no GPU bill                             |
| Grammar fallback | OpenAI GPT-4o-mini                                             | $0.15/1M input tokens; cheap insurance             |
| OCR (S3)         | TrOCR printed + PaddleOCR-ta fallback                          | Best open option for Tamil printed text            |
| Eval             | `jiwer` (CER/WER) + BLEU + native-speaker rubric               | Standard NLP + qualitative                         |
| Storage          | Supabase Postgres (free) + Cloudflare R2 (free tier)           | Free up to limits sufficient for V1                |
| Hosting          | Vercel Hobby (web) + Fly.io free (API) + Hetzner CX32 (Ollama) | All within $50/mo                                  |
| CI               | GitHub Actions: lint + pytest + vitest + build                 | Mandatory per SDLC rule                            |
| Telemetry        | PostHog free + Sentry free                                     | Generous free tiers                                |

## 7. Repos (two-repo strategy, per user decision)

| Repo                               | Owner       | Purpose                                                           | Visibility                                       |
| ---------------------------------- | ----------- | ----------------------------------------------------------------- | ------------------------------------------------ |
| `chandralabs/tamil-edu-toolkit`    | chandralabs | Engine (transliterate/grammar/ocr) + apps (web, iOS) + Python SDK | **Public** (OSS)                                 |
| `chandralabs/<aost-site-repo>`     | chandralabs | Existing static AOST website                                      | **Existing** (one new `/tools` page added in S5) |
| `chandralabs/tamil-llama`          | chandralabs | Existing — Tamil-LLaMA model fork                                 | unchanged                                        |
| `chandralabs/Tamil-Research-LLM`   | chandralabs | Existing — research paper & benchmarks                            | unchanged; cross-linked from new repo            |
| `CaSc-6385/AcademyofSmartThinkers` | CaSc-6385   | Existing Arduino sketches                                         | unchanged                                        |

### tamil-edu-toolkit/ layout

```
tamil-edu-toolkit/
├── apps/
│   ├── web/                  Next.js (kid theme, marketing copy embedded)
│   ├── mobile/               Expo iOS (Android post-V1)
│   └── api/                  FastAPI service
├── packages/
│   ├── ui/                   Shared design tokens (web only V1; NativeWind for mobile in S4)
│   ├── sdk-ts/               TypeScript client for web + mobile
│   ├── transliterate/        IndicXlit wrapper (Python)
│   ├── grammar/              Ollama client + GPT fallback + prompts (Python)
│   ├── ocr/                  TrOCR + Paddle pipeline (Python, S3)
│   └── pylib/                Public Python SDK → PyPI in S6
├── data/
│   ├── golden/               1000-pair Tanglish→Tamil eval set
│   └── augmentation/         Scraped + hand-curated phrase pairs
├── eval/
│   ├── run.py                Harness — emits CER/WER/BLEU + native-rating
│   └── reports/              One markdown report per eval run
├── infra/
│   ├── ollama-hetzner/       Dockerfile + bootstrap script for LLM box
│   └── flyio/                fly.toml for API
├── docs/
│   ├── PLAN.md               This file
│   ├── DEVELOPMENT.md
│   ├── TESTING.md
│   ├── DEPLOYMENT.md
│   └── SPRINTS.md
├── .github/workflows/
│   ├── ci.yml                lint + test + build
│   ├── deploy-web.yml
│   ├── deploy-api.yml
│   └── eval-nightly.yml      Run golden eval nightly, post report
├── pnpm-workspace.yaml       (monorepo TS/JS)
├── pyproject.toml            (monorepo Python via uv/poetry)
└── README.md
```

## 8. Cost model — strict $50/mo budget

| Item                                      | Cost/mo        | Notes                                                         |
| ----------------------------------------- | -------------- | ------------------------------------------------------------- |
| Vercel Hobby (web)                        | $0             | Free for hobby/personal                                       |
| Fly.io API (free tier)                    | $0             | 3 shared VMs, 256MB each — fine for FastAPI                   |
| **Hetzner CX32 (Ollama for Tamil-LLaMA)** | **~$8**        | 4 vCPU, 8GB RAM, Frankfurt; runs Q4_K_M 7B at ~5-10 tok/s     |
| Supabase Free                             | $0             | 500MB DB, 1GB storage, 50k MAU                                |
| Cloudflare R2 Free                        | $0             | 10GB storage, 1M Class A ops/mo                               |
| Domain (already owned)                    | $0             | Subdomain only                                                |
| OpenAI GPT-4o-mini fallback               | **~$10**       | Only on Ollama overload; capped at $15 via OPENAI_USAGE_LIMIT |
| OCR API (S3 stretch)                      | $0             | Self-hosted TrOCR/Paddle on same Hetzner box                  |
| Apple Developer Program                   | $99/yr ≈ $8/mo | For iOS App Store (S4)                                        |
| Sentry Free + PostHog Free                | $0             | Generous free tiers                                           |
| **TOTAL EXPECTED**                        | **~$26/mo**    |                                                               |
| **HARD CAP**                              | **$50/mo**     | Alert at $35; pause non-essential at $45                      |

**Budget guardrails (enforced in code):**

- `OPENAI_MONTHLY_BUDGET_USD=15` env var; middleware checks running total and disables fallback above cap (returns Ollama-only with longer wait UX)
- Hetzner billing alert at €30
- Vercel build-minutes alert at 80% of free quota
- Monthly cost report committed to `eval/reports/cost-YYYY-MM.md`

## 9. Risks & mitigations

| Risk                                                       | Likelihood | Mitigation                                                                           |
| ---------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------ |
| Ollama on CPU too slow for realtime (>3s p95)              | Med        | GPT-4o-mini fallback gated on latency; cache common phrases                          |
| Aksharantar struggles on code-switch (English in Tanglish) | High       | Token-classifier: detect English via dict, preserve verbatim                         |
| Apple App Store rejection (kids category compliance)       | Med        | COPPA-clean V1: no PII, no accounts; submit early in S4                              |
| AOST site repo not found → blocked on S5 integration       | Med        | Subdomain works independently; static `/tools` page can be PR'd once repo identified |
| $50 budget breached                                        | Low        | Hard cap in code; monthly cost report                                                |
| Native-speaker grammar rating below 4/5                    | Med        | A/B between Tamil-LLaMA + GPT-4o-mini; pick winner per category                      |
| Scope creep (especially mobile S4)                         | High       | Strict MoSCoW; cut "Should" items if S2 slips                                        |

## 10. Definition of Done (per story, every sprint)

Per user's SDLC rule (no stubs, tests required, branch sync at end):

1. Code merged to `main` via PR (no direct pushes)
2. Unit tests added; line coverage ≥ 80% on new code
3. Integration test if crossing a service boundary
4. Eval metric recorded if it changes model output (in `eval/reports/`)
5. Docs updated if user-facing
6. Demo GIF / screenshot in PR description
7. CI green (lint + test + build + eval-smoke)
8. Cost impact noted in PR if architecture changes

## 11. Open questions (do not block planning)

1. **AOST website repo location** — not found in `chandralabs` or `CaSc-6385`. Need user to confirm exact repo name so S5-3 (`/tools` page PR) can be planned.
2. **Mascot name** — placeholder "சித்து / Chittu" used in plan; needs branding decision before S1 design.
3. **Apple Developer account** — does chandralabs have one? If not, factor in 1–2 day enrollment lead time before S4 ends.
4. **DNS provider for academyofsmartthinkers.com** — need access to add `tamil.` CNAME in S5-1.

## 12. Versioning

- **v1 (superseded)**: web-only Tanglish translator on `tamil-edu-toolkit` standalone.
- **v2 (superseded)**: full umbrella monorepo `asot-platform` with mobile + STEM migration.
- **v3 (FROZEN, this doc)**: two-repo, web+iOS, AOST subdomain integration, $50 budget cap.

Any change to scope, repo strategy, or budget → bump to v4 and copy this file.
