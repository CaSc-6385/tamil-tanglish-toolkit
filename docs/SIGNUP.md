# Signup steps for S1-8 + S1-9 deploys

Three free accounts to create. **Total time: ~15 minutes.** All on free tiers, no credit card required for any (Fly.io may ask for verification but doesn't charge).

When done, add the four secrets to GitHub repo settings (Settings → Secrets and variables → Actions → New repository secret). Then a push to `main` will auto-deploy everything.

## 1. Vercel — for the web frontend (`apps/web` → Next.js)

**~3 minutes.**

1. Go to **<https://vercel.com/signup>** → "Continue with GitHub" → sign in as the same GitHub account that owns `chandralabs/tamil-edu-toolkit`.
2. After signup, click **"Add New… → Project"**.
3. **"Import Git Repository"** → find `chandralabs/tamil-edu-toolkit` → click **Import**.
   - If you don't see the repo: click "Adjust GitHub App Permissions" → grant access to `tamil-edu-toolkit`.
4. **Configure Project** page:
   - **Framework Preset**: Next.js _(auto-detected from `vercel.json`)_
   - **Root Directory**: leave blank _(vercel.json handles it)_
   - **Build Command**: leave default
   - **Environment Variables** — click "Add" for each:
     | Name | Value |
     |---|---|
     | `NEXT_PUBLIC_API_URL` | `https://tamil-edu-api.fly.dev` |
     | `NEXT_PUBLIC_POSTHOG_KEY` | _(paste from PostHog step 3 below — leave empty for now if you want)_ |
     | `NEXT_PUBLIC_POSTHOG_HOST` | `https://us.i.posthog.com` |
5. Click **Deploy**. Build takes ~2 min.
6. When done, you get a URL like `https://tamil-edu-toolkit-<hash>.vercel.app`.

**You're done — Vercel auto-deploys on every push to `main` from now on. No CI token needed.**

Optional: set a friendlier URL like `tamil-edu-web.vercel.app` under Project → Settings → Domains.

---

## 2. Fly.io — for the API backend (`apps/api` → FastAPI)

**~5 minutes.**

1. Go to **<https://fly.io/app/sign-up>** → sign up with GitHub or email.
   - Fly may ask for a credit card for "account verification" — they don't charge unless you exceed the free tier (3 shared-cpu VMs / 160GB egress).
2. Install the Fly CLI locally:
   ```powershell
   # Windows PowerShell
   iwr https://fly.io/install.ps1 -useb | iex
   ```
3. Sign in from CLI:
   ```powershell
   fly auth login
   ```
   Opens browser, authorizes you.
4. **Create the app** (one-time, from the repo root):
   ```powershell
   cd C:\work\tamil-edu-toolkit
   fly apps create tamil-edu-api --org personal
   ```
   _(If `tamil-edu-api` is taken, pick a unique name and update `apps/api/fly.toml` line `app = "..."`.)_
5. **Create a deploy token** for GitHub Actions:
   ```powershell
   fly tokens create deploy --app tamil-edu-api --expiry 90d
   ```
   Copy the long string starting with `fo1_` — that's your `FLY_API_TOKEN`.

**Add to GitHub**: Settings → Secrets and variables → Actions → New repository secret

- Name: `FLY_API_TOKEN`
- Value: _(paste the token)_

Next push to `main` touching `apps/api/**` or `packages/transliterate/**` will deploy automatically. Or trigger manually: Actions tab → "Deploy API (Fly.io)" → Run workflow.

---

## 3. PostHog — for telemetry (S1-9)

**~3 minutes.**

1. Go to **<https://us.posthog.com/signup>** → sign up with GitHub or email.
2. After signup, you'll be in a default project. **Settings (gear icon) → Project → Project ID and API key**.
3. Copy the **Project API Key** (starts with `phc_`).
4. Paste into Vercel: **Vercel → tamil-edu-toolkit project → Settings → Environment Variables → edit `NEXT_PUBLIC_POSTHOG_KEY`** → paste the `phc_...` key → Save.
5. Trigger a redeploy: Vercel → Deployments → latest → "Redeploy".

That's it. PostHog will start receiving `translate.requested` / `translate.succeeded` / `translate.error` events from real users. Dashboard at `https://us.posthog.com/insights`.

**No GitHub secret needed** — PostHog key is public-safe (it's `NEXT_PUBLIC_*`, exposed in the JS bundle by design).

---

## 4. (Optional) Custom subdomain — `tamil.academyofsmartthinkers.com`

When the above is working, point the AOST subdomain to Vercel:

1. **Vercel** → Project → Settings → Domains → Add `tamil.academyofsmartthinkers.com`. Vercel shows you the DNS record needed (a CNAME).
2. **GoDaddy** (your AOST DNS provider) → DNS Management → add a CNAME:
   - Type: `CNAME`
   - Name: `tamil`
   - Value: `cname.vercel-dns.com.` (or whatever Vercel showed you)
   - TTL: 1 hour
3. Wait ~5 min for DNS propagation. Vercel auto-issues an SSL cert.

Now both URLs work: `https://tamil.academyofsmartthinkers.com` and `https://tamil-edu-toolkit-*.vercel.app`.

---

## Checklist — what to send back here

When done, tell me:

| Done? | Item                                                | What to share                                     |
| ----- | --------------------------------------------------- | ------------------------------------------------- |
| [ ]   | Vercel project created + first deploy succeeded     | The URL (e.g. `tamil-edu-toolkit-abc.vercel.app`) |
| [ ]   | Fly app created (`fly apps create tamil-edu-api`)   | "app created" — no token needed in chat           |
| [ ]   | `FLY_API_TOKEN` added to GitHub repo secrets        | "FLY_API_TOKEN set"                               |
| [ ]   | PostHog project key added to Vercel env vars        | "PostHog wired"                                   |
| [ ]   | Vercel env var `NEXT_PUBLIC_API_URL` set to Fly URL | "API URL set"                                     |

I'll then trigger the API deploy from Actions and we'll have everything live. Total wait after your signups: ~5 min.

---

## Cost summary

| Service   | Plan       | Cost                                      |
| --------- | ---------- | ----------------------------------------- |
| Vercel    | Hobby      | **$0** (100GB bandwidth/mo, plenty)       |
| Fly.io    | Free       | **$0** (3 shared-cpu-256MB VMs; we use 1) |
| PostHog   | Cloud Free | **$0** (1M events/mo)                     |
| **Total** |            | **$0/mo**                                 |

Well within the $50/mo PLAN.md budget cap (we're using $0 of it for S1-8 + S1-9).
