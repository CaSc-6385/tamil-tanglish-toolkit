# Development Plan

Engineering practices for `chandralabs/tamil-edu-toolkit`. Aligned with PLAN.md v3 (frozen).

## 1. Methodology — Agile, sprint-based

- **Sprint length**: 2 weeks (except S0 = 3 days, foundations only).
- **Capacity assumption**: solo developer, ~15 hr/week. Adjust velocity if team grows.
- **Sprint ritual**:
  - Day 1: write sprint backlog into GitHub Issues, label `sprint-N`, milestone-link
  - Daily: 5-min self-standup in PR comments ("what shipped / what's next / blockers")
  - End-of-sprint Friday: demo recording + retro markdown in `docs/retros/sprint-N.md`
- **Definition of Ready** (story can enter sprint): clear acceptance criteria, estimated, dependencies known.
- **Definition of Done**: see PLAN.md §10.

## 2. Branching — trunk-based with short-lived branches

```
main                                 ← always deployable; protected
 ├── feat/s1-typed-translator        ← per-story branch
 ├── fix/s1-confidence-tooltip       ← bugfix branch
 └── chore/s0-ci-pipeline
```

- **No long-lived develop / release branches** (overhead not worth it for solo dev).
- Feature branches **must be merged within 5 working days** of creation.
- Squash-merge to keep history flat; PR title becomes commit subject.
- `main` is protected: requires CI green + 1 approval (self-approve OK on solo PRs but force you to review your own diff).

## 3. Commit conventions — Conventional Commits

```
feat(transliterate): handle code-switched English tokens
fix(api): correct CORS on /translate
chore(ci): add ruff to lint workflow
docs(plan): bump to v3
test(eval): add 50 conversation-domain golden pairs
```

Types: `feat | fix | chore | docs | test | refactor | perf | build | ci`.
Scope is the package or app. Body explains _why_. Footer references issue: `Refs #42`.

## 4. PR rules

- **Size**: target ≤ 400 LoC diff; hard cap 800. Bigger → split.
- **Description template** (`.github/pull_request_template.md`):
  - What changed and why
  - Linked issue(s)
  - DoD checklist (all 8 items from PLAN §10)
  - Demo GIF/screenshot
  - Cost impact (if any)
- **Required CI checks**: lint, test, build, eval-smoke (eval-nightly is separate).
- **Self-review rule**: even on solo PRs, open the "Files changed" tab and add ≥ 1 review comment before merging — forces a second look.

## 5. Code style

| Language         | Linter                          | Formatter     | Pre-commit |
| ---------------- | ------------------------------- | ------------- | ---------- |
| Python           | `ruff check`                    | `ruff format` | yes        |
| TypeScript / TSX | `eslint` + `@typescript-eslint` | `prettier`    | yes        |
| Markdown         | `markdownlint`                  | `prettier`    | yes        |
| YAML             | `yamllint`                      | `prettier`    | yes        |

- `pre-commit` hooks installed via `.pre-commit-config.yaml` (run on `git commit`).
- CI re-runs all linters; pre-commit is just for fast local feedback.
- **No `# type: ignore` or `// @ts-ignore` without an issue link in the comment.**

## 6. Issue tracking — GitHub Issues + Projects

- One **GitHub Project** (board): "Tamil Edu Toolkit Sprints". Columns: Backlog · Ready · In Progress · In Review · Done.
- Each story = one Issue. Labels: `sprint-0`…`sprint-6`, `must`/`should`/`could`, area (`area:web` / `area:mobile` / `area:api` / `area:ml` / `area:infra` / `area:docs`).
- Issue template includes: User story (As X, I want Y, so that Z), Acceptance criteria (Given/When/Then), Out of scope.
- Bug template: repro steps, expected, actual, severity (P0 prod down → P3 cosmetic).

## 7. Dependency hygiene

- **Dependabot** weekly PRs for npm + pip + GitHub Actions. Auto-merge patch versions if CI green.
- **No new dependency without an issue justifying it** (no impulse adds).
- **License audit** on every dep: MIT / Apache-2.0 / BSD only. GPL/AGPL requires approval.
- **Lockfiles committed** (`pnpm-lock.yaml`, `uv.lock` or `poetry.lock`).

## 8. Environment & secrets

- `.env.example` checked in; **never** commit real `.env`.
- Local secrets: `.env.local`, gitignored.
- CI / prod secrets: GitHub Actions secrets (org-level when possible).
- Required vars documented in `docs/CONFIG.md` (to be created in S0).
- No secrets in logs. Sentry beforeSend strips known keys.

## 9. Folder ownership (CODEOWNERS)

```
*                           @schandra
apps/web/                   @schandra
apps/mobile/                @schandra
apps/api/                   @schandra
packages/grammar/           @schandra   # touches model serving, extra care
packages/ocr/               @schandra
data/golden/                @schandra   # eval set changes need review
infra/                      @schandra   # cost-impacting
```

Update when collaborators join.

## 10. Local development setup (to be scripted in S0)

Required tools:

- Node 20 + pnpm 9
- Python 3.11 + `uv` (faster than poetry)
- Docker (for Ollama local dev)
- `pre-commit`
- `gh` CLI

`make bootstrap` (S0-3 deliverable):

1. Installs pre-commit hooks
2. `pnpm install` at root
3. `uv sync` in each Python package
4. Pulls Ollama Tamil-LLaMA GGUF: `ollama pull abhinand/tamil-llama-7b-instruct:q4_k_m`
5. Copies `.env.example` → `.env.local`
6. Seeds local Postgres with golden eval subset

`make dev` runs:

- `apps/web` on :3000
- `apps/api` on :8000
- `ollama serve` on :11434

## 11. Documentation discipline

- **Every package** has a `README.md` with: purpose, install, usage example, public API.
- **`docs/` is the source of truth** for cross-cutting decisions (PLAN, DEVELOPMENT, TESTING, DEPLOYMENT, SPRINTS).
- **ADRs (Architecture Decision Records)** in `docs/adr/NNNN-title.md` for non-trivial choices. Template: Context · Decision · Consequences. First ADR: `0001-use-ollama-not-modal.md` (justifies cost decision in PLAN.md §5).

## 12. Anti-patterns to avoid

(From user's `feedback_sdlc_process.md` rule: no stubs, no half-finished work, tests required.)

- ❌ Merging a PR with a `TODO: implement later` in the critical path
- ❌ Adding a feature flag to hide unfinished work in prod
- ❌ Skipping tests "because it's just a small change"
- ❌ Bypassing pre-commit hooks (`--no-verify`)
- ❌ Direct push to `main`
- ❌ Letting a feature branch live > 5 days
- ❌ Adding a dependency without an issue
