# @tamil-edu/web

Next.js 14 (App Router) web UI for the Tamil education toolkit.

## Run

```bash
# from repo root
make dev          # boots web on :4000 + api on :8000

# or just the web
pnpm --filter @tamil-edu/web dev
```

Open http://localhost:4000.

## Config

| Env var               | Default                 | What                            |
| --------------------- | ----------------------- | ------------------------------- |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Base URL of the FastAPI service |

Copy `.env.example` to `.env.local` to override.

## Tests

```bash
pnpm --filter @tamil-edu/web test   # vitest
pnpm --filter @tamil-edu/web typecheck
```

## Layout

```
app/
├── globals.css       Tailwind + Noto Sans Tamil
├── layout.tsx        Root layout
└── page.tsx          Translator UI (textarea → translate → output)
lib/
├── api.ts            fetch wrapper around POST /translate
└── api.test.ts       vitest mocks for the client
```
