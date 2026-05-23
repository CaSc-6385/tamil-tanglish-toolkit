# syntax=docker/dockerfile:1.6
# Multi-arch ready. Build at repo root:
#   docker build -f apps/api/Dockerfile -t tamil-edu-api .
# Fly.io builds this via .github/workflows/deploy-api.yml on push to main.

FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install uv for fast deps resolution
RUN pip install uv==0.4.30

# Copy workspace metadata first so deps install layer caches
COPY pyproject.toml ./
COPY apps/api/pyproject.toml apps/api/
COPY packages/transliterate/pyproject.toml packages/transliterate/

# Copy source so uv sync can install workspace members in editable mode
COPY packages/transliterate/src packages/transliterate/src
COPY apps/api/src apps/api/src

# Install runtime deps (skip dev extras to keep image lean)
RUN uv sync --no-dev


FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    TRANSLITERATE_BACKEND=aksharamukha \
    CORS_ORIGINS=""

WORKDIR /app

# Copy the resolved venv + source from builder
COPY --from=builder /app /app

# Non-root user (Fly free-tier doesn't care but it's defense in depth)
RUN useradd -r -u 1000 -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)" || exit 1

CMD ["uvicorn", "tamil_edu_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
