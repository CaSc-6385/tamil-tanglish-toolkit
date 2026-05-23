# Deployment Plan

Infra + release strategy for `chandralabs/tamil-edu-toolkit`. Aligned with PLAN.md v3 (frozen) and the **$50/mo hard budget cap**.

## 1. Environments

| Env         | Purpose                | Audience                | Web URL                            | API URL                                | Branch           |
| ----------- | ---------------------- | ----------------------- | ---------------------------------- | -------------------------------------- | ---------------- |
| **local**   | dev workstation        | developer               | `localhost:3000`                   | `localhost:8000`                       | feature branches |
| **dev**     | per-PR preview         | reviewer                | `<pr-N>.tamil-edu.vercel.app`      | `dev.api.tamil-edu.fly.dev`            | PR branch        |
| **staging** | end-to-end pre-release | internal raters         | `staging.tamil-edu.vercel.app`     | `staging.api.tamil-edu.fly.dev`        | `main`           |
| **prod**    | public release         | kids, parents, teachers | `tamil.academyofsmartthinkers.com` | `api.tamil.academyofsmartthinkers.com` | tag `v*.*.*`     |

- **Dev** = automatic on PR open (Vercel preview deploys); ephemeral API on Fly.io with `-dev` suffix.
- **Staging** = auto-deploy on merge to `main`.
- **Prod** = manual promote on git tag `v0.1.0`, `v0.2.0`, …

## 2. Infra map

```
                        Internet
                           │
        ┌──────────────────┼──────────────────┐
        ▼                                      ▼
┌────────────────┐                  ┌──────────────────┐
│ Vercel         │                  │ Fly.io           │
│ Next.js        │ ── fetch ──▶     │ FastAPI (256MB)  │
│ (web app)      │                  │ free tier ×3     │
└────────────────┘                  └────────┬─────────┘
                                             │
                       ┌─────────────────────┼──────────────────────┐
                       ▼                     ▼                      ▼
                  ┌─────────┐         ┌─────────────┐       ┌──────────────┐
                  │ Hetzner │         │  Supabase   │       │ OpenAI       │
                  │ CX32    │         │  Postgres   │       │ GPT-4o-mini  │
                  │ Ollama  │         │  free       │       │ (fallback)   │
                  │ + TrOCR │         └─────────────┘       └──────────────┘
                  └─────────┘                                       │
                                                         budget-capped at $15
```

## 3. Per-component deployment

### 3.1 Web (Next.js → Vercel)

- **Project**: `tamil-edu-toolkit-web`, linked to GitHub repo
- **Build**: `pnpm --filter web build`
- **Preview deploys**: every PR; URL posted to PR by Vercel bot
- **Prod**: `main` deploys to `staging.`; tag `v*.*.*` triggers GitHub Action that does `vercel --prod` with prod env vars
- **Custom domain**: `tamil.academyofsmartthinkers.com` (S5-1)
- **Env vars** (set in Vercel UI): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_POSTHOG_KEY`, `SENTRY_DSN`
- **Free tier limits**: 100GB bandwidth, 6000 build minutes / mo — sufficient

### 3.2 API (FastAPI → Fly.io)

- **App name**: `tamil-edu-api` (prod), `-staging`, `-dev`
- **Region**: `iad` (US East — closest to OpenAI East endpoint)
- **VM**: `shared-cpu-1x` 256MB — free tier (3 VMs total across all apps)
- **Image**: built in GitHub Actions, pushed to Fly's registry
- **Health check**: `GET /health` returns Ollama + DB reachability
- **Scaling**: 1 instance V1; autoscale 1–3 after launch metrics stabilize
- **Env vars** (set via `fly secrets set`):
  ```
  OLLAMA_URL=http://<hetzner-ip>:11434
  OLLAMA_MODEL=abhinand/tamil-llama-7b-instruct:q4_k_m
  OPENAI_API_KEY=sk-...
  OPENAI_MONTHLY_BUDGET_USD=15
  SUPABASE_URL=https://...
  SUPABASE_SERVICE_KEY=...
  SENTRY_DSN=...
  POSTHOG_KEY=...
  ```

### 3.3 Tamil-LLaMA serving (Ollama → Hetzner CX32)

- **Server**: Hetzner CX32 (4 vCPU AMD, 8GB RAM, 80GB disk), Frankfurt — **€4.99/mo (~$5.40)**
- **OS**: Ubuntu 24.04 LTS
- **Bootstrap script** (`infra/ollama-hetzner/bootstrap.sh`):
  1. `apt update && upgrade`
  2. `ufw allow 22; ufw allow from <fly-egress-ips> to any port 11434; ufw enable`
  3. Install Ollama
  4. `ollama pull abhinand/tamil-llama-7b-instruct:q4_k_m`
  5. Systemd unit for `ollama serve`
  6. Fail2ban for SSH
  7. Caddy reverse proxy with mutual TLS to Fly
- **Backup**: weekly snapshot via Hetzner Cloud (+€0.50/mo)
- **Monitoring**: Hetzner built-in CPU/RAM alerts at 80%
- **Sized for**: ~5–10 tokens/sec on Q4_K_M 7B; supports ~3 concurrent users at p95 < 3s for 50-token corrections
- **Scale-up trigger**: if p95 > 3s for 24h sustained → upgrade to CX42 (€8/mo)

### 3.4 OCR (TrOCR + Paddle, S3)

- **Co-located on Hetzner CX32 initially** (same box as Ollama, separate process port 8001)
- If RAM contention → split to CX22 dedicated OCR box (€3.79/mo)
- Triggered async via `POST /ocr` → background task → result polled by client

### 3.5 Mobile iOS (Expo → App Store)

- **Build**: EAS Build (Expo cloud) — free tier 30 builds/mo
- **Distribution**:
  - Internal: EAS Internal Distribution (no App Store review) for sprint demos
  - TestFlight: end of S4 (Apple review ~1 day)
  - App Store: end of S5 (Apple review 1–3 days, factor in)
- **Apple Developer Program**: $99/year ≈ $8/mo
- **Bundle ID**: `com.academyofsmartthinkers.tamil`
- **Update strategy**: Expo OTA for JS-only changes (instant); store submission only for native deps changes

### 3.6 Database & storage

- **Postgres**: Supabase free tier (500MB DB, 2GB egress, 50k MAU) — sufficient for V1 (history + cost ledger + native-rater queue)
- **Object storage**: Cloudflare R2 free tier (10GB) for OCR upload retention (24h TTL, then purged)
- **Migrations**: `alembic` for Python-side schema; one migration per PR; reversible

## 4. CI/CD pipelines (GitHub Actions)

### 4.1 `ci.yml` (per PR)

```
- checkout
- setup-pnpm + setup-python (uv)
- pnpm install --frozen-lockfile
- uv sync
- lint (ruff, eslint, prettier --check)
- test:python (pytest --cov --cov-fail-under=80 on diff)
- test:ts (vitest run --coverage)
- build:web (next build)
- build:api (docker build)
- eval-smoke (eval/run.py --sample 10)
```

### 4.2 `deploy-web.yml` (push to main → staging; tag v\* → prod)

```
- if event=push & ref=main → vercel pull staging && vercel deploy --prod-of staging
- if event=tag & ref=refs/tags/v* → vercel pull prod && vercel deploy --prod
```

### 4.3 `deploy-api.yml` (same trigger split)

```
- docker build
- docker push to fly registry
- fly deploy -a tamil-edu-api(-staging)  with --strategy rolling
```

### 4.4 `eval-nightly.yml` (cron 03:00 UTC)

```
- run eval/run.py against the full v1 golden set
- commit report to eval/reports/
- compare to previous run; if any metric regressed >2pp → open issue, label P1, assign self
```

### 4.5 `cost-monthly.yml` (cron 1st of month 06:00 UTC)

```
- query OpenAI usage API, Hetzner billing, Vercel/Fly usage
- emit eval/reports/cost-YYYY-MM.md
- commit and open issue if month-to-date > $35
```

## 5. Release process

Per sprint (every 2 weeks):

1. **Friday morning**: merge final PRs of the sprint
2. **Friday noon**: run eval-nightly manually; native-rater queue clears
3. **Friday afternoon**: bump version, tag `v0.X.0`, push tag
4. **GitHub Action** auto-deploys prod web + api
5. **Smoke test** prod within 30 min: 5 hand-tested translations, OCR if S3+, mobile if S4+
6. **Demo recording** posted
7. **Retro** committed
8. **Mon morning**: sprint planning for N+1 begins

### Hotfix process

- Branch from prod tag: `hotfix/v0.X.1`
- Minimal diff
- Skip non-critical CI (still run lint+test+build); skip eval-nightly
- Tag `v0.X.1` immediately; same auto-deploy path

## 6. Rollback strategy

| Layer         | Rollback path                                                               | RTO      |
| ------------- | --------------------------------------------------------------------------- | -------- |
| Web           | `vercel rollback <deployment-id>` (or revert tag + redeploy)                | < 5 min  |
| API           | `fly releases list` → `fly deploy --image <prev>`                           | < 10 min |
| DB schema     | `alembic downgrade -1` (only if migration is reversible — that's a PR rule) | < 5 min  |
| Ollama model  | Keep last 2 model tags; `systemctl restart ollama` with prev                | < 15 min |
| Mobile JS     | Expo OTA: publish previous release branch                                   | < 10 min |
| Mobile native | Store rollback not possible — fix forward via emergency build               | ~24h     |

## 7. Monitoring & alerts

| Tool                         | What                            | Alert threshold                            |
| ---------------------------- | ------------------------------- | ------------------------------------------ |
| **Sentry** (free)            | Errors, perf                    | New issue spike → email                    |
| **PostHog** (free)           | Funnels, event success rate     | Drop > 10% day/day → email                 |
| **Better Stack** (free tier) | Uptime checks: web, api, ollama | Down 2 min → email                         |
| **Hetzner billing**          | Server cost                     | Alert at €15 month-to-date (over baseline) |
| **OpenAI usage**             | API cost                        | Hard cap $15 in code; alert at $10         |
| **Vercel**                   | Build minutes, bandwidth        | Alert at 80% of free tier                  |
| **Fly.io**                   | VM hours, bandwidth             | Alert at 80% of free tier                  |

All alerts to `academyofsmartthinkers@gmail.com` (existing channel) and `schandra@ieee.org`.

## 8. Secrets management

- **Local**: `.env.local` (gitignored)
- **CI**: GitHub Actions secrets, scoped per env
- **Vercel**: env vars in dashboard, scoped to preview/staging/prod
- **Fly.io**: `fly secrets set` (encrypted at rest)
- **Hetzner box**: secrets in `/etc/tamil-edu.env` (chmod 600); Ansible-managed
- **No secrets in repo, ever.** Pre-commit `detect-secrets` hook.

## 9. Domain & DNS

- **Parent domain**: `academyofsmartthinkers.com` (already owned by user, per confirmation)
- **DNS provider**: TBD — need to identify in S5-0 (likely Cloudflare or Namecheap)
- **Subdomain**: `tamil.academyofsmartthinkers.com` — CNAME to `cname.vercel-dns.com`
- **API subdomain**: `api.tamil.academyofsmartthinkers.com` — CNAME to Fly's edge
- **MX / email**: unchanged (preserves Gmail)
- **TLS**: auto via Vercel + Fly + Caddy on Hetzner

## 10. Cost ledger (live, updated monthly in `eval/reports/cost-YYYY-MM.md`)

| Service            | Plan             | $/mo        | Hard cap             |
| ------------------ | ---------------- | ----------- | -------------------- |
| Vercel             | Hobby            | $0          | —                    |
| Fly.io             | Free 3 VMs       | $0          | —                    |
| Hetzner CX32       | dedicated Ollama | ~$5.40      | $8 (upgrade trigger) |
| Hetzner backups    | weekly snapshot  | ~$0.55      | $1                   |
| Supabase           | Free             | $0          | —                    |
| Cloudflare R2      | Free 10GB        | $0          | —                    |
| OpenAI GPT-4o-mini | pay-as-you-go    | ~$5–10      | **$15 (enforced)**   |
| Apple Developer    | annual           | ~$8         | $9                   |
| Sentry             | Free             | $0          | —                    |
| PostHog            | Free 1M events   | $0          | —                    |
| Better Stack       | Free             | $0          | —                    |
| **Expected total** |                  | **~$19–24** |                      |
| **Hard cap**       |                  |             | **$50**              |

If any month's cost exceeds $35 — open a P1 issue, write a post-mortem, adjust before next sprint.
