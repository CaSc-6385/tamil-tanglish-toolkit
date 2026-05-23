# Repository configuration

The canonical record of GitHub settings applied to `chandralabs/tamil-edu-toolkit`. Reconcile periodically against the live repo. If something here disagrees with the live repo, the live repo wins until this doc is updated.

Last reconciled: 2026-05-23 (S0-6).

## Basic

| Setting | Value | Rationale |
|---|---|---|
| Visibility | **PRIVATE** (open question — see PLAN.md v3 §7 + memory) | Pending resolution before S6 (PyPI publish requires public) |
| Default branch | `main` | Modern default |
| Description | "Tanglish to Tamil translator for kids learning the language. Web and iOS. Part of Academy of Smart Thinkers." | |
| Homepage | https://www.academyofsmartthinkers.com/ | |
| Topics | `tamil`, `transliteration`, `nlp`, `tanglish`, `kids-education`, `tamil-llama`, `ollama`, `nextjs`, `fastapi`, `expo` | Discovery |

## Features

| Feature | State | Why |
|---|---|---|
| Issues | **enabled** | Sprint tracking (PLAN.md §11, DEVELOPMENT.md §6) |
| Projects | **enabled** | "Tamil Edu Toolkit Sprints" board (S0-10) |
| Wiki | **disabled** | All docs live in `docs/`, single source of truth |
| Discussions | disabled (V1) | Re-enable post-launch if community grows |
| Sponsorships | disabled | Not yet — revisit at v1.0.0 |

## Merge / PR settings

| Setting | Value | Why |
|---|---|---|
| Allow squash merging | **enabled** (default) | Keeps history flat (DEVELOPMENT.md §2) |
| Allow merge commits | **disabled** | Forces squash; cleaner log |
| Allow rebase merging | **disabled** | Forces squash |
| Automatically delete head branches | **enabled** | Cleanup after merge |
| Always suggest updating PR branches | enabled | Avoids stale-base merges |
| Allow auto-merge | enabled | Useful for tiny Dependabot PRs once green |

## Branch protection — `main`

| Rule | Value | Why |
|---|---|---|
| Require a pull request before merging | **yes** | No direct pushes (DEVELOPMENT.md §2) |
| Required approving reviews | **0** | Solo dev — self-approve impossible on GitHub; rely on CI |
| Dismiss stale approvals on new pushes | yes | Forces re-review when diff changes |
| Require review from Code Owners | yes | CODEOWNERS-driven |
| Require status checks to pass | **yes** | Below |
| Require branches to be up to date | yes | Catches base drift |
| Require conversation resolution | yes | No leaking unresolved comments to `main` |
| Require linear history | yes | Squash-merge implies this |
| Require signed commits | not yet (V1) | Add when first external contributor lands |
| Lock branch | no | Need to be able to merge |
| Do not allow bypassing the above | **no** | Admin bypass allowed for emergencies |
| Restrict who can push to matching branches | no | Solo |
| Allow force pushes | **no** | Never on main |
| Allow deletions | **no** | Never on main |

### Required status checks (all from `.github/workflows/ci.yml`)

- `Lint Python (ruff)`
- `Lint JS/TS + Markdown (prettier)`
- `Test Python (pytest)`
- `Test JS/TS (vitest, where present)`
- `Eval smoke (10 golden pairs)`
- `Build (next + docker)`
- `Pre-commit hooks`

If you rename a job in `ci.yml`, **update this list AND the branch protection rule** — GitHub gates on the literal job name.

## Secrets (Actions → Secrets and variables → Actions)

Set as needed per sprint. Empty until S1+.

| Secret | Used by | Set in sprint |
|---|---|---|
| `CODECOV_TOKEN` | `test-python` upload | S0 (optional — CI tolerates absence) |
| `OPENAI_API_KEY` | grammar fallback | S2 |
| `OLLAMA_URL` | grammar primary | S2 |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | API | S2 |
| `SENTRY_DSN` | observability | S1 |
| `POSTHOG_KEY` | telemetry | S1 |
| `VERCEL_TOKEN` | web deploy | S1 |
| `FLY_API_TOKEN` | API deploy | S1 |
| `EXPO_TOKEN` | mobile EAS | S4 |
| `APPLE_APP_STORE_KEY` | App Store submit | S4 |

## Webhooks

None for V1. Future: Slack / Discord notifications on deploy events (post-launch).

## Maintenance

- Reconcile this doc on every settings change. If you touch the repo settings via the GitHub UI, update the corresponding row here in the same commit.
- Re-run the branch-protection script in `infra/repo-settings/apply.sh` (added later) to recover from accidental UI changes.
