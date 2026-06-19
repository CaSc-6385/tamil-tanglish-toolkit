# AOST Tamil — Tanglish → Tamil, with understanding 🌸

> Type **Tanglish** (Tamil in English letters) → get correct **Tamil**, broken down
> word-by-word with **part of speech + meaning + a picture emoji** so kids actually
> _understand_ it. Read text straight from a **photo**. 100% **free and local** — no
> API keys, no cloud, runs on your own machine.

Built for the **Tanglish-to-Tamil Translator** hackathon (Students track), under the
[Academy of Smart Thinkers](https://www.academyofsmartthinkers.com/).

---

## What it does

| Feature                            | Example                                                                                                     |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **1. Understand-and-translate**    | `nettru naan nadakumboothu oru naai kuraichuthu` → **நேற்று நான் நடந்துகொண்டிருந்தபோது ஒரு நாய் குரைத்தது** |
| **2. Pictorial grammar breakdown** | 🙋 நான் `pronoun` "I" · 🐶 நாய் `noun` "dog" · 🗣️ குரைத்தது `verb` "barked"                                 |
| **3. Image OCR**                   | Drop a photo of printed Tamil/Tanglish → text is extracted and translated                                   |

It doesn't just transliterate letter-by-letter (which gets `nettru` wrong as
`நெட்ரு`). It **understands the sentence** and writes natural Tamil — then explains
the grammar with colours and pictures so a learner can follow along.

> **Add a screenshot / demo GIF here** — run the app (below), then record with
> `Cmd+Shift+5` on macOS and drop the file in `docs/` as `demo.gif`.

---

## How the models work (the "merge")

Each step uses the open model that is best at it — all served locally by **Ollama**:

```
 Tanglish text ─┐
 (or a photo) ──┤
                ▼
        ┌───────────────┐   image
        │  Tesseract 5  │◀── OCR (Tamil + Latin)
        └──────┬────────┘
               ▼ text
        ┌──────────────────────────┐
        │  gemma2:9b  (Ollama)      │  ① understand casual phonetic Tanglish
        │  meaning-based prompt     │     → correct, natural Tamil
        └──────┬───────────────────┘
               ▼ Tamil sentence
        ┌──────────────────────────┐
        │  gemma2:9b  (Ollama)      │  ② per-word breakdown → JSON
        │  POS + gloss + emoji      │     {tamil, pos, gloss, emoji}
        └──────┬───────────────────┘
               ▼
     Next.js UI: translation + colour-coded pictorial grammar cards
```

- **Translation** — `gemma2:9b` with a meaning-based, few-shot prompt that teaches the
  common phonetic spellings, fixes verb tenses, and preserves negation. (We also ship
  a `sarvam` backend wrapping
  [`sarvamai/sarvam-translate`](https://huggingface.co/sarvamai/sarvam-translate), but
  found it too literal for casual Tanglish — gemma2 understands meaning far better.)
- **Grammar / structure** — a second `gemma2` call returns each word's part of speech,
  a short English gloss, and one picture emoji.
- **OCR** — Tesseract 5 (LSTM, `tam+eng`), CPU-only.

Everything is **pluggable** behind small Python packages, so a model can be swapped
with one env var (`OLLAMA_MODEL`, `OCR_BACKEND`, `ANALYZE_TRANSLATE_BACKEND`).

---

## Quickstart

**Prereqs:** [Ollama](https://ollama.com), Tesseract, Node 20+, [uv](https://docs.astral.sh/uv/).

```bash
# 1. models + OCR engine (one time)
ollama pull gemma2:9b
brew install tesseract tesseract-lang        # macOS  (apt: tesseract-ocr tesseract-ocr-tam)

# 2. install deps
uv sync --all-extras
corepack pnpm install                        # or: npm i -g pnpm && pnpm install

# 3. run (two terminals)
TRANSLITERATE_BACKEND=ollama OCR_BACKEND=tesseract \
  uv run uvicorn --app-dir apps/api/src tamil_edu_api.main:app --port 8000
pnpm --filter web dev                        # → http://localhost:3000
```

Open **http://localhost:3000**, type some Tanglish, and hit **Translate & explain**.
(First request loads gemma2 into memory; expect ~15s, then faster.)

---

## Architecture

A pnpm + `uv` monorepo:

```
apps/
  web/                 Next.js 14 + Tailwind (dark, kid-friendly, accessible)
  api/                 FastAPI — POST /translate · /analyze · /ocr · /health
packages/
  transliterate/       Tanglish→Tamil backends (ollama/gemma2, sarvam, aksharamukha, baseline)
  grammar/             per-word POS + gloss + emoji analyzer  (NEW)
  ocr/                 Tesseract image→text                   (NEW)
eval/                  golden set + Tanglish quality harness
```

**API:** `POST /analyze {text}` → `{ tamil, words:[{tamil,pos,gloss,emoji}], … }` is the
comprehensive endpoint; `POST /translate` and `POST /ocr` are also available.

**Tech:** Next.js 14 · Tailwind · FastAPI · Pydantic · Ollama · gemma2 · Tesseract ·
Sarvam-Translate (optional). All open-source and free.

---

## Quality — honest eval

We ran **108 diverse Tanglish sentences** (`eval/tanglish_eval.py`): greetings, all
tenses, questions, emotions, code-switching, negation.

- **~85–90% of common learner sentences** translate correctly and naturally.
- The meaning-based prompt fixed the big failure modes — **negation no longer flips**
  (`naan saapdala` → சாப்பிட**வில்லை** ✓), common loanwords translate (`sweet`→இனிப்பு,
  `bus`→பேருந்து), and output stays in Tamil.
- **Known limits** (a 9B local model, not Google Translate): very ambiguous phonetic
  spellings (`siri` smile vs சிறிது little), rare words, and the occasional foreign-script
  glitch. Latency is ~15s for the full translate-+-breakdown on CPU/Ollama.

Run it yourself: `uv run python eval/tanglish_eval.py`.

---

## Tests

```bash
uv run pytest          # Python: ~204 tests across api + packages, ≥80% coverage
pnpm --filter web test # Web: vitest
pnpm --filter web build
```

---

## Credits

- Scaffolding & architecture: the [chandralabs/tamil-edu-toolkit](https://github.com/chandralabs/tamil-edu-toolkit) base (MIT).
- Models: [`gemma2`](https://huggingface.co/google/gemma-2-9b-it) (Google),
  [`sarvam-translate`](https://huggingface.co/sarvamai/sarvam-translate) (Sarvam AI),
  [Tesseract](https://github.com/tesseract-ocr/tesseract).
- Tamil-LLaMA / research: [chandralabs/tamil-llama](https://github.com/chandralabs/tamil-llama).

## License

[MIT](LICENSE)
