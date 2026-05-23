# Tamil Edu Toolkit

> Tanglish → Tamil for kids learning to write the language. Web and iOS. Open source. Part of [Academy of Smart Thinkers](https://www.academyofsmartthinkers.com/).

[![Status](https://img.shields.io/badge/status-sprint--0-orange)](docs/SPRINTS.md)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-frozen--v3-green)](docs/PLAN.md)

## What this is

Type **Tanglish** ("vanakkam nanba"), get back correct **Tamil Unicode** (`வணக்கம் நண்பா`) with grammar-aware correction. Designed for Tamil-learning kids 8–13, their parents, and Tamil-school teachers.

**Stretch**: drag-drop a photo of printed Tamil text → cleaned Tamil output via OCR.

## How it's different from Vāṇi

[Vāṇi](https://vaanieditor.com/) is an excellent Tamil-in → Tamil-out proofreader for adult journalists, authors, and publishers. **This toolkit is complementary**: Tanglish/image-in → Tamil-out **production**, built for kids. Different direction, different audience, no head-on overlap.

## Architecture

See [docs/PLAN.md](docs/PLAN.md) for the frozen v3 master plan.

Quick summary: Next.js web → FastAPI → IndicXlit (transliteration) → Tamil-LLaMA via Ollama on Hetzner CPU (grammar) → GPT-4o-mini fallback (budget-capped). iOS via Expo arrives in Sprint 4. Strict $50/mo infra budget.

## Status

Sprint 0 — repo scaffolding. No product code yet. See:

- [PLAN.md](docs/PLAN.md) — frozen master plan (vision, scope, architecture, costs)
- [SPRINTS.md](docs/SPRINTS.md) — S0 through S6 backlog with acceptance criteria
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) — agile process, branching, code style
- [TESTING.md](docs/TESTING.md) — test pyramid, ML eval methodology
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) — environments, CI/CD, cost ledger

## Quickstart (placeholder — fleshed out in S0-2)

```bash
make bootstrap   # install deps, pull Ollama model, set up pre-commit
make dev         # web on :3000, api on :8000
make test        # pytest + vitest
make eval        # run golden eval set
```

## Related work

- [chandralabs/tamil-llama](https://github.com/chandralabs/tamil-llama) — Tamil-LLaMA fork (Llama-2 base + Tamil tokenizer + 145k instructions; GGUF Q4_K_M ~4GB runs on CPU)
- [chandralabs/Tamil-Research-LLM](https://github.com/chandralabs/Tamil-Research-LLM) — research paper and benchmarks justifying the model choice ("Modern way of Education: Tamil LLM usage in Tamil Education")
- [Academy of Smart Thinkers](https://www.academyofsmartthinkers.com/) — STEM education organization this toolkit lives under

## Contributing

Sprint 0 only — accepting contributions starts at v0.1.0 (end of Sprint 1). See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for branching and PR rules once we're open.

## License

[MIT](LICENSE) © 2026 chandralabs
