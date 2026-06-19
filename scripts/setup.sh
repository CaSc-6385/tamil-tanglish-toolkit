#!/usr/bin/env bash
# One-command setup for AOST Tamil. Installs everything the app needs:
# Ollama + the gemma2 model, Tesseract (Tamil OCR), uv/Node/pnpm, and all deps.
# Idempotent — skips anything already installed. macOS (Homebrew) + Linux (apt).
set -euo pipefail

# Make freshly-installed tools visible without re-opening the shell.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

MODEL="${OLLAMA_MODEL:-gemma2:9b}"
say() { printf "\n\033[1;33m▶ %s\033[0m\n" "$*"; }
ok() { printf "  \033[1;32m✓ %s\033[0m\n" "$*"; }
have() { command -v "$1" >/dev/null 2>&1; }

OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
  PKG="brew"
  if ! have brew; then
    echo "Homebrew is required on macOS. Install it from https://brew.sh then re-run." >&2
    exit 1
  fi
elif [ "$OS" = "Linux" ]; then
  PKG="apt"
  if ! have apt-get; then
    echo "This script supports Debian/Ubuntu (apt). Install Ollama, Tesseract(+tam)," \
      "uv, Node 20+, and pnpm manually, then run 'uv sync --all-extras && pnpm install'." >&2
    exit 1
  fi
else
  echo "Unsupported OS '$OS'. On Windows use WSL2 (Ubuntu) and re-run." >&2
  exit 1
fi

install_pkg() {
  if [ "$PKG" = "brew" ]; then brew install "$@"; else sudo apt-get install -y "$@"; fi
}

# 1. Ollama -------------------------------------------------------------------
say "Ollama (local model runtime)"
if have ollama; then
  ok "already installed"
else
  if [ "$PKG" = "brew" ]; then brew install ollama; else curl -fsSL https://ollama.com/install.sh | sh; fi
  ok "installed"
fi
# start the server if it isn't answering
if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  say "Starting the Ollama server"
  (ollama serve >/tmp/ollama.log 2>&1 &) || true
  for _ in $(seq 1 30); do
    curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1 && break
    sleep 1
  done
fi
curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1 && ok "server running"

# 2. The model ----------------------------------------------------------------
say "Model: $MODEL (~5.4 GB, one time)"
if curl -fsS http://localhost:11434/api/tags 2>/dev/null | grep -q "${MODEL%%:*}"; then
  ok "already pulled"
else
  ollama pull "$MODEL"
  ok "pulled"
fi

# 3. Tesseract + Tamil --------------------------------------------------------
say "Tesseract OCR + Tamil data (optional photo feature)"
if have tesseract && tesseract --list-langs 2>/dev/null | grep -qx tam; then
  ok "already installed with Tamil"
elif [ "$PKG" = "brew" ]; then
  install_pkg tesseract tesseract-lang && ok "installed"
else
  install_pkg tesseract-ocr tesseract-ocr-tam && ok "installed"
fi

# 4. Dev tooling --------------------------------------------------------------
say "uv (Python package manager)"
have uv && ok "already installed" || { curl -LsSf https://astral.sh/uv/install.sh | sh; ok "installed"; }

say "Node.js 20+"
if have node; then ok "already installed ($(node --version))"; else install_pkg node && ok "installed"; fi

say "pnpm"
have pnpm && ok "already installed" || { npm install -g pnpm && ok "installed"; }

# 5. Dependencies -------------------------------------------------------------
say "Python dependencies (uv sync)"
uv sync --all-extras
ok "done"

say "Web dependencies (pnpm install)"
pnpm install
ok "done"

printf "\n\033[1;32m✅ Setup complete!\033[0m  Now run:  \033[1m./scripts/run.sh\033[0m\n\n"
