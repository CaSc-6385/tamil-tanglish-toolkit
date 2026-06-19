.PHONY: help setup demo bootstrap dev test lint format build typecheck eval clean
.DEFAULT_GOAL := help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup:  ## One-command install: Ollama + model + Tesseract + all deps
	./scripts/setup.sh

demo:  ## One-command launch: start API + web, open the browser (Ctrl+C to stop)
	./scripts/run.sh

bootstrap:  ## One-time dev setup: install all deps + pre-commit hooks
	@command -v pnpm >/dev/null 2>&1 || { echo "pnpm not found — install Node 20+ and corepack enable"; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "uv not found — see https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
	@command -v pre-commit >/dev/null 2>&1 || { echo "pre-commit not found — pip install pre-commit"; exit 1; }
	pnpm install
	uv sync --all-extras
	pre-commit install
	@echo ""
	@echo "Bootstrap complete. Next: make dev (once apps exist in S1) or make eval"

dev:  ## Run local dev servers (apps/web on :4000, apps/api on :8000)
	@if [ ! -d apps/api ] || [ ! -d apps/web ]; then \
		echo "Apps not scaffolded yet. Run 'make bootstrap' first."; \
		exit 1; \
	fi
	pnpm dev

test:  ## Run all tests (Python + TS)
	uv run pytest
	pnpm test

lint:  ## Lint all code (ruff + eslint + prettier)
	uv run ruff check .
	uv run ruff format --check .
	pnpm lint

format:  ## Auto-format all code
	uv run ruff format .
	uv run ruff check . --fix
	pnpm format

typecheck:  ## TypeScript typecheck across workspaces
	pnpm typecheck

build:  ## Build all apps + packages
	pnpm build

eval:  ## Run the golden-set eval harness (CER/WER/BLEU)
	uv run python -m eval.run --model baseline --sample 10

clean:  ## Remove build artifacts and caches
	find . -type d \( -name __pycache__ -o -name .pytest_cache -o -name .ruff_cache -o -name .mypy_cache -o -name .next -o -name dist -o -name build \) -prune -exec rm -rf {} +
	find . -type f \( -name "*.pyc" -o -name ".coverage" -o -name "coverage.xml" \) -delete
	@echo "Cleaned."
