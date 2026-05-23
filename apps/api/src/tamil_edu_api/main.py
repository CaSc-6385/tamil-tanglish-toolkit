"""FastAPI app — POST /translate wraps the transliterate library.

Run locally:
    uv run uvicorn tamil_edu_api.main:app --reload --port 8000

Default backend is `baseline` (passthrough, no model download). To use the real
IndicXlit model, install the extra and set the env var:
    uv add 'tamil-edu-transliterate[indicxlit]'
    $env:TRANSLITERATE_BACKEND = "indicxlit"   # PowerShell
    export TRANSLITERATE_BACKEND=indicxlit     # bash
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tamil_edu_transliterate import TransliterationError, transliterate

from tamil_edu_api import __version__
from tamil_edu_api.models import HealthResponse, TranslateRequest, TranslateResponse

# ---- Config (env-var driven) ----

BACKEND = os.environ.get("TRANSLITERATE_BACKEND", "baseline").strip().lower()
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Validate backend choice at boot — fail fast on misconfig."""
    if BACKEND not in {"baseline", "indicxlit"}:
        raise RuntimeError(
            f"TRANSLITERATE_BACKEND={BACKEND!r} is invalid. Use 'baseline' or 'indicxlit'."
        )
    yield


app = FastAPI(
    title="tamil-edu-api",
    version=__version__,
    description="Tanglish → Tamil transliteration service.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", backend=BACKEND, version=__version__)


@app.post("/translate", response_model=TranslateResponse, tags=["translate"])
async def translate_endpoint(req: TranslateRequest) -> TranslateResponse:
    start = time.perf_counter()
    try:
        tamil = transliterate(req.text, backend=BACKEND, topk=req.topk)
    except TransliterationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:  # unknown backend or bad input
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Alternatives via the backend's protocol method, separately
    alternatives: list[str] = []
    if req.topk > 1:
        try:
            from tamil_edu_transliterate import _get  # type: ignore[attr-defined]

            alternatives = _get(BACKEND).alternatives(req.text, topk=req.topk)
        except (TransliterationError, ValueError):
            # Surfacing alternatives is best-effort; don't fail the whole request.
            alternatives = [tamil]

    duration_ms = int((time.perf_counter() - start) * 1000)
    return TranslateResponse(
        tamil=tamil,
        alternatives=alternatives,
        backend=BACKEND,
        duration_ms=duration_ms,
    )
