# Sprint Plan — Frozen v3

Aligned with PLAN.md v3, DEVELOPMENT.md (agile, trunk-based), TESTING.md (gates), DEPLOYMENT.md (envs).

- **Pace**: agile, 2-week sprints (S0 is a 3-day foundations sprint).
- **Order**: Web first (S1–S3), iOS second (S4), AOST integration (S5), distribution (S6).
- **Capacity assumption**: solo dev, ~15 hr/week. 7 sprints × 2 weeks = ~14 weeks (~3.5 months) to V1.0.
- **Backlog source**: each story below becomes a GitHub Issue with sprint label.
- **Per-story DoD**: PLAN.md §10. Per-sprint exit gates: TESTING.md §6.

---

## Sprint 0 — Foundations (3 days, week 0)

**Goal**: monorepo + CI + golden eval set + budget guardrails. Zero product code yet.

| ID | Story | Acceptance |
|---|---|---|
| S0-1 | Create `chandralabs/tamil-edu-toolkit` repo (public, MIT, README) | Repo live; README links to Tamil-Research-LLM paper, vaanieditor, tamil-llama |
| S0-2 | Monorepo scaffolding: `pnpm-workspace.yaml`, `uv` workspace, `Makefile` with `bootstrap`/`dev`/`test`/`lint` | `make bootstrap && make dev` boots web + api locally |
| S0-3 | CI pipeline (`.github/workflows/ci.yml`) — lint + test + build + eval-smoke | Green on empty repo |
| S0-4 | Build golden eval set v1 (1000 pairs, 5 domains × 200) | `data/golden/v1.csv` committed + checksum file |
| S0-5 | Eval harness skeleton (`eval/run.py`) — emits CER/WER/BLEU on a dummy baseline | `python eval/run.py --model baseline --sample 10` runs in <30s |
| S0-6 | Branch protection on `main` + PR template + CODEOWNERS | Settings screenshot in `docs/repo-config.md` |
| S0-7 | Pre-commit hooks + `.pre-commit-config.yaml` | `git commit` runs ruff, prettier, detect-secrets |
| S0-8 | ADR-0001 "Use Ollama for Tamil-LLaMA serving, not Modal" | Committed to `docs/adr/0001-use-ollama-not-modal.md` |
| S0-9 | Budget guardrail middleware skeleton (`OPENAI_MONTHLY_BUDGET_USD`) | Unit test confirms request blocked above cap |
| S0-10 | GitHub Project board "Tamil Edu Toolkit Sprints" with 5 columns; S1 stories drafted | Board public; S1 issues created in Backlog |

**S0 exit gate**: every item above merged; CI green on `main`; `docs/` complete.

---

## Sprint 1 — Typed Tanglish Web MVP (2 weeks)

**Goal**: working web demo that converts typed Tanglish to Tamil Unicode at deployed URL, with measurable accuracy.

| ID | Story | Acceptance |
|---|---|---|
| S1-1 | `packages/transliterate`: integrate IndicXlit Tamil model | `transliterate(text)->str`; 50 unit tests; CER ≤ 15% on smoke set |
| S1-2 | Code-switch handling: detect English tokens, preserve verbatim | "Send Ravi an email" → tokens correctly classified; 30 unit tests |
| S1-3 | `apps/api`: `POST /translate` endpoint (Pydantic in/out, OpenAPI doc) | 10 contract tests via httpx |
| S1-4 | `apps/web`: kid-themed UI (large fonts, mascot placeholder, textarea, output panel, copy/download buttons) | Lighthouse a11y ≥ 90; axe-core 0 violations |
| S1-5 | Per-word confidence display (color-coded) + alt-suggestion tooltip | Hover shows top-3 alternatives |
| S1-6 | History (localStorage only — no account, COPPA-safe) | Last 20 translations persist across reload |
| S1-7 | Eval run on golden set v1; publish baseline report | `eval/reports/2026-MM-DD-s1-baseline.md` committed |
| S1-8 | Deploy: Vercel staging + Fly.io API staging | `staging.tamil-edu.vercel.app` reachable; smoke pass |
| S1-9 | PostHog event instrumentation: `translate.requested`, `translate.succeeded`, error rate | Dashboard linked in README |

**S1 exit gate**: CER ≤ 12% on golden v1; p95 latency < 800ms; staging URL public.

---

## Sprint 2 — Grammar-aware correction layer (2 weeks)

**Goal**: Tamil-LLaMA-based correction layer running on Hetzner Ollama, with GPT-4o-mini fallback.

| ID | Story | Acceptance |
|---|---|---|
| S2-1 | Provision Hetzner CX32; deploy Ollama; pull `tamil-llama-7b-instruct:q4_k_m` | `curl ollama:11434/api/generate` returns Tamil text |
| S2-2 | `packages/grammar`: `correct(tamil_text)->str` via Ollama HTTP | 30 unit tests with mocked client; integration test against live |
| S2-3 | Prompt engineering: 20-shot examples from `Tamil-Research-LLM` grammar dataset | Prompts committed to `packages/grammar/prompts.py` |
| S2-4 | GPT-4o-mini fallback path; gated on latency > 3s OR queue depth > 5 | A/B test report; cost per call logged |
| S2-5 | Budget enforcement: hard-block GPT calls above `OPENAI_MONTHLY_BUDGET_USD` | Test confirms 429 returned at cap |
| S2-6 | API: `POST /translate?correct=true` returns raw + corrected | Contract test; OpenAPI updated |
| S2-7 | Web UI: correction toggle; side-by-side diff view; keyboard shortcut Ctrl+G | Toggle persists per session |
| S2-8 | Phrase cache in Postgres (Supabase): cache hits skip both Ollama + OpenAI | Cache hit rate ≥ 40% after 100 mixed requests |
| S2-9 | Native-rater queue: 100-sample slice queued in Postgres; CLI for rater | Rater workflow doc in `docs/rater-guide.md` |
| S2-10 | Eval run with correction enabled; publish report | Report in `eval/reports/`; CER ≤ 7%; native rating ≥ 4/5 on 80% of samples |

**S2 exit gate**: CER ≤ 7%; native-rater 80% ≥ 4; OpenAI spend ≤ $10 this sprint.

---

## Sprint 3 — OCR + Web polish (2 weeks)

**Goal**: drag-drop printed Tamil/Tanglish image → cleaned Tamil text. Production-ready web app.

| ID | Story | Acceptance |
|---|---|---|
| S3-1 | `packages/ocr`: TrOCR printed-Tamil pipeline | F1 ≥ 0.85 on 100 printed test images |
| S3-2 | PaddleOCR-ta fallback (auto-selected when TrOCR confidence < threshold) | Integration test; report in `eval/reports/ocr-s3.md` |
| S3-3 | Deploy OCR service co-located with Ollama on Hetzner CX32 | Health check passes; RAM headroom > 1GB |
| S3-4 | API: `POST /ocr` (multipart upload) → returns text + per-line confidence | Contract tests; image size cap 10MB |
| S3-5 | Web UI: drag-drop zone, image preview, OCR → transliterate → correct chain | E2E test via Playwright |
| S3-6 | Rate limiting: 60 req/IP/hour; friendly 429 page | Tested with rate-limit-attack script |
| S3-7 | Tamil text-to-speech for output (browser SpeechSynthesis API) | Toggleable; falls back gracefully on unsupported browsers |
| S3-8 | Mascot artwork + animations (placeholder → finalized "சித்து / Chittu") | Artwork in `apps/web/public/mascot/`; Storybook entry |
| S3-9 | Dark mode + light mode + system-pref detection | Toggle + persists |
| S3-10 | Streaks + word-of-the-day (light gamification) | Streak counter persists in localStorage; word-of-day rotates daily |
| S3-11 | Lighthouse perf ≥ 80 on mobile profile | Report in PR description |

**S3 exit gate**: end-to-end image→corrected Tamil ≤ 5s p95; web app rated production-quality.

---

## Sprint 4 — iOS Mobile App MVP (2 weeks)

**Goal**: TestFlight-live iOS app with type/voice/camera input. (Android trivially follows from Expo build, but not store-submitted in V1.)

| ID | Story | Acceptance |
|---|---|---|
| S4-1 | `apps/mobile`: Expo SDK 51 scaffold + NativeWind | `expo start` boots; theme parity with web |
| S4-2 | Shared `packages/sdk-ts`: TypeScript client for `/translate`, `/correct`, `/ocr` | Used by both web and mobile; vitest |
| S4-3 | Type screen: textarea → translate → corrected output (same API as web) | Maestro smoke test |
| S4-4 | Voice input: `expo-av` mic → upload audio → server-side Whisper-Tamil | Whisper on Hetzner CX32 (whisper.cpp small.en/ta); E2E test |
| S4-5 | Camera screen: `expo-camera` snap → upload to `/ocr` → translate → correct | Maestro E2E |
| S4-6 | Bundled IndicXlit ONNX (distilled, ~30MB) for offline transliteration | Toggle in settings; CER ≤ 15% on smoke |
| S4-7 | Mascot, streaks, word-of-day parity with web | Visual diff |
| S4-8 | EAS Build pipeline (iOS) → TestFlight Internal | TestFlight build available to invited testers |
| S4-9 | App Store metadata: screenshots, description, kids-category compliance, COPPA privacy policy URL | Submission package ready in `apps/mobile/store/` |
| S4-10 | PostHog RN SDK instrumentation parity with web | Same events emitted |
| S4-11 | Submit to App Store review (end of sprint, to overlap with S5) | Submitted; status tracked |

**S4 exit gate**: TestFlight live with all M-features; App Store submission in review.

---

## Sprint 5 — AOST Integration (2 weeks)

**Goal**: subdomain live with AOST brand; web + iOS app rebranded; existing AOST site links to it.

| ID | Story | Acceptance |
|---|---|---|
| S5-0 | **Resolve open question**: locate existing AOST website repo; confirm DNS provider | Documented in `docs/repo-config.md` |
| S5-1 | DNS: add `tamil.academyofsmartthinkers.com` CNAME → Vercel; `api.tamil.academyofsmartthinkers.com` → Fly | Both resolve; SSL active |
| S5-2 | AOST brand kit: logo, color tokens, typography (Noto Sans Tamil + Inter); apply to web | Visual diff vs. existing AOST site (cohesive) |
| S5-3 | Submit PR to existing AOST website repo: add `/tools.html` page linking to `tamil.academyofsmartthinkers.com` | PR open; merged once approved |
| S5-4 | Submit PR to update `/research` page: cross-link to live Tamil tool | PR open; merged |
| S5-5 | iOS app store listing: name "AOST Tamil", AOST branding in icons + splash + screenshots | App Store version released (or pending review) |
| S5-6 | Parent/teacher view: simple read-only dashboard showing child's recent translations (localStorage export → email link) | Feature flagged behind `?parent=1` query string for V1 |
| S5-7 | COPPA compliance audit: privacy policy page, data minimization checklist, no third-party trackers without consent | Published at `tamil.academyofsmartthinkers.com/privacy` |
| S5-8 | Launch post on `academyofsmartthinkers.blogspot.com` | Draft reviewed; published with demo embed |
| S5-9 | Demo video (2 min) for YouTube `@thegeniuskid-greatestchann5030` | Uploaded; linked from app footer + README |
| S5-10 | Update Tamil-Research-LLM README to cross-link the product | PR open in that repo |

**S5 exit gate**: a kid lands on academyofsmartthinkers.com → clicks Tools → reaches translator → converts a phrase. iOS app branded "AOST Tamil" in store.

---

## Sprint 6 — Distribution & Open Source (2 weeks)

**Goal**: open-source the engine and ship secondary channels (Chrome ext, PyPI, RapidAPI).

| ID | Story | Acceptance |
|---|---|---|
| S6-1 | Polish `tamil-edu-toolkit` README for OSS: badges, quickstart, contribution guide, CoC | Repo passes GitHub community standards checks |
| S6-2 | `packages/pylib`: thin Python SDK wrapping the API | Published to PyPI as `tamil-edu-toolkit`; `pip install tamil-edu-toolkit` works |
| S6-3 | `apps/extension`: Chrome MV3 right-click "Translate Tanglish → Tamil" on any selected text | Chrome Web Store submission in review |
| S6-4 | RapidAPI listing for `/translate`, `/correct`, `/ocr` | Listing live; free tier 100 req/day, paid tier $0.001/req |
| S6-5 | School-license CTA on landing page (email opt-in, no payment in V1) | Form active; submissions saved to Supabase |
| S6-6 | Telemetry retrospective: cost report, usage funnel, top errors → roadmap for v0.2 | Report in `docs/v1-launch-retro.md` |
| S6-7 | Press: ProductHunt launch, r/tamil post, Tamil Sunday school outreach email | Launched; track signups |
| S6-8 | Tag `v1.0.0` release | GitHub release with assets; release notes |

**S6 exit gate**: v1.0.0 tagged; 4 channels live (web, iOS, Chrome ext, PyPI); first 100 real users; cost ≤ $50 for the month.

---

## Backlog (post-V1, ranked)

1. Android Play Store release (Expo build already works; needs only store submission)
2. Custom Tanglish iOS keyboard (system-wide, types Tamil in any app)
3. Handwriting OCR (TrOCR fine-tuned on Tamil script)
4. Voice → Tamil with on-device Whisper Tiny (truly offline)
5. Dialect selector (Madras / Jaffna / Sri Lankan)
6. Bulk PDF/DOCX teacher worksheet conversion
7. Open the golden eval set as a HuggingFace dataset
8. Vāṇi API export integration (advanced users → downstream proofread)
9. Migrate existing AOST static site to Next.js as v2 of integration

---

## Capacity & timeline

| Sprint | Duration | Cumulative |
|---|---|---|
| S0 | 3 days | wk 0 |
| S1 | 2 wks | wk 2 |
| S2 | 2 wks | wk 4 |
| S3 | 2 wks | wk 6 |
| S4 | 2 wks | wk 8 |
| S5 | 2 wks | wk 10 |
| S6 | 2 wks | wk 12 |

**Target v1.0.0 release**: ~12–14 weeks from S0 start. If solo capacity drops below 15 hr/wk, cut "Should" items first (per MoSCoW); don't compress sprints.

## Velocity tracking

Per sprint, record in `docs/retros/sprint-N.md`:
- Planned story points / actual
- Carry-over count
- Hours actually spent
- One thing to keep, one to change
