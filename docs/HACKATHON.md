# AOST Tamil — Hackathon Submission

**Track**: For Students → _Tanglish to Tamil Translator_
**Team / Org**: [Academy of Smart Thinkers](https://www.academyofsmartthinkers.com/)
**Submitted by**: chandralabs (schandra@ieee.org)

|                            |                                                                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 🌐 **Live demo**           | <https://tamil-edu-toolkit.vercel.app>                                                                                                  |
| 🔌 **Live API**            | <https://tamil-edu-api.fly.dev> ([docs](https://tamil-edu-api.fly.dev/docs))                                                            |
| 📦 **Source**              | <https://github.com/chandralabs/tamil-edu-toolkit>                                                                                      |
| 📊 **Eval report**         | [v1 / 70-pair golden set](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/eval/reports/2026-05-23-205115-aksharamukha-v1.md) |
| 📐 **Architecture / Plan** | [docs/PLAN.md](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/PLAN.md) (frozen v3)                                     |

---

## 1. The problem

Every Tamil-learning kid — diaspora, urban India, Sri Lanka — types **Tanglish** (Tamil written in English letters) on WhatsApp, Instagram, school messaging. Converting "vanakkam nanba" to "வணக்கம் நண்பா" by hand requires:

- Knowing the Tamil keyboard layout
- Remembering which "n" is dental (ன) vs retroflex (ண)
- Distinguishing short/long vowels with diacritics

Existing tools either target adult journalists (paid: [Vāṇi](https://vaanieditor.com/), ~₹100/mo) or are dumb rule-based transliterators (Google Input Tools) with no Tanglish awareness.

**No tool serves the kid-learning-Tamil audience.** That's what we built.

## 2. What we shipped

A working web app + API at <https://tamil-edu-toolkit.vercel.app>:

- **Kid-friendly UI**: large fonts, playful color palette, sample-phrase chips, mascot-ready (placeholder), localStorage history (COPPA-safe, no accounts).
- **Code-switch aware**: type "send the message ku reply pannu" → English words pass through verbatim, only Tanglish gets transliterated.
- **Per-word alternatives**: click any Tamil word → popover with top-3 candidate transliterations → click to swap. Real per-word data flows from API to UI.
- **Pluggable backends**: 4 transliteration engines selectable at runtime:
  1. `baseline` — passthrough (eval floor)
  2. `aksharamukha` — rule-based, deployed default (real Tamil, CER 35% on golden set)
  3. `openai-gpt` — GPT-4o-mini (production-quality, gated on API key)
  4. `indicxlit` — ai4bharat ML model ([blocked upstream](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/adr/0002-indicxlit-deferred.md), ready to swap when fairseq unblocks)
- **End-to-end deployed**:
  - Web: Vercel (Next.js 14 + Tailwind + Noto Sans Tamil)
  - API: Fly.io (FastAPI in Docker, auto-sleep, CORS preset)
  - Cost: **$0/mo** on free tiers (Vercel Hobby + Fly Free + future PostHog Free)

## 3. Try it now (30 seconds)

1. Open <https://tamil-edu-toolkit.vercel.app>
2. Click sample chip **[vanakkam nanba]**
3. Click **Translate to Tamil**
4. See Tamil output appear with backend + timing
5. Try a code-switched phrase: **send the message ku reply pannu** → English words preserved, Tanglish converted

## 4. Architecture

```
┌────────────────┐   POST /translate     ┌─────────────────────┐
│  Next.js Web   │ ────────────────────▶ │  FastAPI Service    │
│  Vercel CDN    │ ◀──── JSON ────────── │  Fly.io shared-CPU  │
└────────────────┘                       └──────────┬──────────┘
                                                    │
                  ┌─────────────────────────────────┼──────────────────────────┐
                  ▼                                 ▼                          ▼
        ┌──────────────────┐            ┌──────────────────┐        ┌──────────────────┐
        │  Tokenizer       │            │   Backends       │        │   Telemetry      │
        │  (S1-2)          │            │   (pluggable)    │        │   PostHog        │
        │                  │            │                  │        │   (S1-9 stub)    │
        │  EN vs Tanglish  │            │  - baseline      │        └──────────────────┘
        │  via ~250-word   │            │  - aksharamukha  │
        │  dictionary +    │            │  - openai-gpt    │
        │  capital-letter  │            │  - indicxlit     │
        │  heuristics      │            │     (blocked)    │
        └──────────────────┘            └──────────────────┘
```

All under a single `Transliterator` Python protocol — swap backends without touching API code.

## 5. Engineering quality (concrete)

| Metric            | Value                                                                                    |
| ----------------- | ---------------------------------------------------------------------------------------- |
| Python tests      | **161 passing** (mocked OpenAI + IndicXlit + aksharamukha)                               |
| TS tests          | 13 passing (vitest, jsdom)                                                               |
| Code coverage     | **91%** (gates at 80%)                                                                   |
| CI workflows      | 2: main CI (7 jobs all green) + nightly eval-real (uploads CER report as artifact)       |
| Deploy workflows  | 1: auto-deploy API on `apps/api/**` change to main; Vercel auto-deploy web on every push |
| Linters           | ruff (Python), prettier (Markdown/YAML/JSON), eslint-via-next (TS), pre-commit hooks     |
| Branch protection | 7 required status checks on `main`, CODEOWNERS, PR template with 8-item DoD              |
| Docs              | 5 design docs (PLAN, DEVELOPMENT, TESTING, DEPLOYMENT, SPRINTS) + 2 ADRs                 |

## 6. What's unique

|                          | **Google Input Tools**        | **Vāṇi**                         | **AOST Tamil (us)**                            |
| ------------------------ | ----------------------------- | -------------------------------- | ---------------------------------------------- |
| Audience                 | Generic                       | Adult journalists                | **Kids 8–13**                                  |
| Pricing                  | Free                          | ₹100/mo                          | **Free + open-source**                         |
| Direction                | Tanglish → Tamil (rule-based) | Tamil-in → Tamil-out (proofread) | **Tanglish → Tamil (kid-aware)**               |
| Code-switch handling     | No                            | N/A                              | **Yes (S1-2 tokenizer)**                       |
| Per-word alternatives UI | No                            | No                               | **Yes (S1-5)**                                 |
| Backend flexibility      | Closed                        | Closed                           | **4 pluggable backends**                       |
| Privacy for kids         | Unclear                       | Standard                         | **COPPA-safe: no accounts, localStorage only** |
| Open source              | No                            | No                               | **MIT, ships on PyPI in S6**                   |

## 7. Quality story (honest)

We attempted to use ai4bharat's IndicXlit (the SOTA open ML model for Tamil transliteration). It is **structurally blocked**: its dependency `fairseq` has a Python 3.11+ incompatibility (mutable-default dataclass bug). We documented the full investigation in [ADR-0002](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/adr/0002-indicxlit-deferred.md) and built a 3-way backend strategy instead:

| Backend                     | Status                              | Quality on golden v1 (70 pairs)        |
| --------------------------- | ----------------------------------- | -------------------------------------- |
| `baseline` (passthrough)    | Always available                    | CER 85% (eval floor)                   |
| `aksharamukha` (rule-based) | **Default in production**           | CER 35% (rule ceiling)                 |
| `openai-gpt` (GPT-4o-mini)  | Available with API key              | Expected CER 5–10% (untested at scale) |
| `indicxlit`                 | Wrapper ready, **blocked upstream** | Target CER ≤ 15% (per S1-1 plan)       |

The eval harness, golden set, and CI workflow are all in place — flipping the default backend is a one-line config change the moment IndicXlit is unblocked or GPT becomes the chosen default.

## 8. Sprint 1 deliverables (per [SPRINTS.md](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/SPRINTS.md))

| Story                                   | Status                                                                                       |
| --------------------------------------- | -------------------------------------------------------------------------------------------- |
| S1-1 IndicXlit Tamil model wrapper      | ✅ Scaffold + 3 alternate backends (aksharamukha shipped, openai-gpt ready, indicxlit ready) |
| S1-2 Code-switch handling               | ✅ ~250-word EN dictionary + ALL-CAPS / brand-name heuristics, 28 tests                      |
| S1-3 FastAPI POST /translate            | ✅ Deployed to Fly.io with /health, /docs, CORS, request validation                          |
| S1-4 Kid-themed web UI                  | ✅ Deployed to Vercel with Tailwind + Noto Sans Tamil                                        |
| S1-5 Per-word confidence + alternatives | ✅ Word dataclass through full stack; clickable per-word popovers                            |
| S1-6 localStorage history               | ✅ Last-20 translations, COPPA-safe, hook with 7 vitest tests                                |
| S1-7 Eval baseline report               | ✅ Real CER published on 70-pair golden v1                                                   |
| S1-8 Deploy                             | ✅ Both Vercel + Fly.io live; auto-deploy on push to main                                    |
| S1-9 PostHog telemetry                  | ⚠️ Code stubs deployed; awaiting PostHog account key                                         |

## 9. Roadmap (next sprints)

- **Sprint 2**: Grammar-aware correction layer using `chandralabs/tamil-llama` (the team's own [LLaMA-2 Tamil model](https://github.com/chandralabs/tamil-llama)) via Ollama on Hetzner CPU
- **Sprint 3**: OCR — drag-drop a photo of printed Tamil → cleaned Tamil text (TrOCR + PaddleOCR-ta)
- **Sprint 4**: iOS app via Expo, shared engine with web
- **Sprint 5**: Full AOST brand integration at `tamil.academyofsmartthinkers.com`
- **Sprint 6**: Distribution — Chrome extension, PyPI package, RapidAPI listing

All planned within a strict **$50/mo infra cost cap** ([DEPLOYMENT.md §10](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/DEPLOYMENT.md#10-cost-ledger-live-updated-monthly-in-evalreportscost-yyyy-mmmd)).

## 10. Why this matters

- **Audience that's underserved**: every existing Tamil tool targets adults. Kids learning Tamil through Tanglish texts have nothing kid-shaped.
- **Open + free**: MIT-licensed, $0/mo on free tiers, deployable by any school.
- **Honest engineering**: when the planned ML model didn't work, we documented why ([ADR-0002](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/adr/0002-indicxlit-deferred.md)), shipped a working substitute, and built the eval harness so we can measurably improve later.
- **Production-grade scaffolding**: branch protection, CODEOWNERS, 161 tests, 91% coverage, two CI workflows, end-to-end deployed in 3 hours of clicks. Not a hackathon throwaway — a real product trajectory.

## 11. Team

| Role                 | Person                                                                                                          |
| -------------------- | --------------------------------------------------------------------------------------------------------------- |
| Engineering          | Chandra Sakthivel (chandralabs)                                                                                 |
| Vision / Sponsorship | [Academy of Smart Thinkers](https://www.academyofsmartthinkers.com/)                                            |
| Tamil LLM research   | [chandralabs/Tamil-Research-LLM](https://github.com/chandralabs/Tamil-Research-LLM) (conference paper attached) |

## 12. Links recap

- **Try the demo**: <https://tamil-edu-toolkit.vercel.app>
- **API**: <https://tamil-edu-api.fly.dev/docs>
- **Source code**: <https://github.com/chandralabs/tamil-edu-toolkit>
- **Master plan**: [docs/PLAN.md](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/PLAN.md)
- **Sprint plan**: [docs/SPRINTS.md](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/docs/SPRINTS.md)
- **Eval report**: [eval/reports/2026-05-23-205115-aksharamukha-v1.md](https://github.com/chandralabs/tamil-edu-toolkit/blob/main/eval/reports/2026-05-23-205115-aksharamukha-v1.md)
- **AOST**: <https://www.academyofsmartthinkers.com/>
- **Tamil-Research-LLM paper**: [PDF in repo](https://github.com/chandralabs/Tamil-Research-LLM/blob/main/Modern%20way%20of%20Education%20Tamil%20LLM%20usage%20in%20Tamil%20Education_.pdf)
