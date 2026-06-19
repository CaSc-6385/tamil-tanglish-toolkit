#!/usr/bin/env bash
# One-command launch for AOST Tamil. Starts the API + web app and opens the browser.
# Stops both cleanly on Ctrl+C. Run ./scripts/setup.sh first.
set -uo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
cd "$(dirname "$0")/.."

MODEL="${OLLAMA_MODEL:-gemma2:9b}"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-4000}"

red() { printf "\033[1;31m%s\033[0m\n" "$*"; }
say() { printf "\n\033[1;33m▶ %s\033[0m\n" "$*"; }

# 1. Ensure Ollama is up + the model is present.
if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  say "Starting Ollama server"
  (ollama serve >/tmp/ollama.log 2>&1 &) || true
  for _ in $(seq 1 30); do curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1 && break; sleep 1; done
fi
if ! curl -fsS http://localhost:11434/api/tags 2>/dev/null | grep -q "${MODEL%%:*}"; then
  red "Model '$MODEL' is not pulled. Run ./scripts/setup.sh (or: ollama pull $MODEL)."
  exit 1
fi

# 2. Free the ports if something is already on them.
for p in "$API_PORT" "$WEB_PORT"; do
  pid="$(lsof -ti tcp:"$p" 2>/dev/null || true)"
  [ -n "$pid" ] && { echo "freeing port $p"; kill -9 $pid 2>/dev/null || true; }
done

PIDS=()
cleanup() { echo; say "Stopping…"; for pid in "${PIDS[@]:-}"; do kill "$pid" 2>/dev/null || true; done; exit 0; }
trap cleanup INT TERM

# 3. Start the API.
say "Starting API on :$API_PORT (model: $MODEL)"
TRANSLITERATE_BACKEND=ollama OCR_BACKEND=tesseract OLLAMA_MODEL="$MODEL" GRAMMAR_MODEL="${GRAMMAR_MODEL:-$MODEL}" \
  uv run uvicorn --app-dir apps/api/src tamil_edu_api.main:app --port "$API_PORT" >/tmp/aost_api.log 2>&1 &
PIDS+=($!)
for _ in $(seq 1 40); do curl -fsS "http://localhost:$API_PORT/health" >/dev/null 2>&1 && break; sleep 1; done
curl -fsS "http://localhost:$API_PORT/health" >/dev/null 2>&1 || { red "API failed to start — see /tmp/aost_api.log"; cleanup; }

# 4. Start the web app.
say "Starting web app on :$WEB_PORT"
pnpm --filter web dev --port "$WEB_PORT" >/tmp/aost_web.log 2>&1 &
PIDS+=($!)
for _ in $(seq 1 60); do curl -fsS "http://localhost:$WEB_PORT" >/dev/null 2>&1 && break; sleep 1; done

# 5. Open the browser.
URL="http://localhost:$WEB_PORT"
printf "\n\033[1;32m✅ Running!\033[0m  Open  \033[1m%s\033[0m   (Ctrl+C to stop)\n\n" "$URL"
if command -v open >/dev/null 2>&1; then open "$URL"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; fi

wait
