# tamil-edu-api

FastAPI service that exposes `POST /translate` (and `/health`, `/docs`).

## Run

```bash
# from repo root
uv run uvicorn tamil_edu_api.main:app --reload --port 8000

# or via make
make dev   # boots both web (:3000) and api (:8000)
```

Then:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Translate: `curl -X POST http://localhost:8000/translate -H "content-type: application/json" -d '{"text":"vanakkam"}'`

## Backend selection

Default is `baseline` (passthrough — proves the wire works, no model download).
For real Tanglish → Tamil:

```bash
uv add 'tamil-edu-transliterate[indicxlit]'   # ~1GB model
$env:TRANSLITERATE_BACKEND = "indicxlit"      # PowerShell
# or
export TRANSLITERATE_BACKEND=indicxlit        # bash
```

## CORS

Open by default to `http://localhost:3000` + `http://127.0.0.1:3000`. Override with
`CORS_ORIGINS=https://a.com,https://b.com`.

## Tests

```bash
uv run pytest apps/api/tests/
```
