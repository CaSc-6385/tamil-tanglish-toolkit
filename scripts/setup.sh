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
node_major() { node --version 2>/dev/null | sed -E 's/v([0-9]+).*/\1/'; }
if have node && [ "$(node_major)" -ge 20 ] 2>/dev/null; then
  ok "already installed ($(node --version))"
elif [ "$PKG" = "brew" ]; then
  brew install node && ok "installed ($(node --version))"
else
  # Debian/Ubuntu's own 'nodejs' package is too old for v20, and there is no package
  # called 'node' — use NodeSource, the standard way to get a current Node on Ubuntu.
  have node && echo "  Node $(node --version) is too old (need 20+); upgrading"
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs && ok "installed ($(node --version))"
fi
have node || { echo "Node install failed. Install Node 20+ manually, then re-run." >&2; exit 1; }

# pnpm via corepack (bundled with Node), pinned to the repo's pnpm@9.12.0 — avoids a
# "latest" pnpm that's too new for the installed Node and crashes on every run.
# We install the shim into ~/.local/bin (first on PATH, set above) rather than plain
# `corepack enable`: Node's bin dir is often root-owned (NodeSource), so a plain enable
# silently fails without sudo — and on WSL the Windows PATH leaks in, so a Windows pnpm
# (which needs a newer Node) wins and crashes with 'node:sqlite'. A user-dir shim that
# is first on PATH guarantees the pinned Linux pnpm is the one that runs.
say "pnpm 9.12.0 (via corepack)"
mkdir -p "$HOME/.local/bin"
corepack enable --install-directory "$HOME/.local/bin" pnpm 2>/dev/null || true
corepack prepare pnpm@9.12.0 --activate
hash -r 2>/dev/null || true
ok "pnpm $(pnpm --version) ($(command -v pnpm))"

# 5. Dependencies -------------------------------------------------------------
say "Python dependencies (uv sync)"
uv sync --all-extras
ok "done"

say "Web dependencies (pnpm install)"
pnpm install
ok "done"

printf "\n\033[1;32m✅ Setup complete!\033[0m  Now run:  \033[1m./scripts/run.sh\033[0m\n\n"
