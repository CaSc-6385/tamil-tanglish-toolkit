"""FastAPI app — POST /translate wraps the transliterate library.

Run locally:
    uv run uvicorn tamil_edu_api.main:app --reload --port 8000

Default backend is `aksharamukha` (rule-based, real Tamil output). Other options
via env var:
    TRANSLITERATE_BACKEND=baseline    # passthrough (testing / no model)
    TRANSLITERATE_BACKEND=aksharamukha # rule-based real Tamil (default)
    TRANSLITERATE_BACKEND=indicxlit   # ML model — currently blocked (ADR-0002)
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tamil_edu_transliterate import TransliterationError, _get  # type: ignore[attr-defined]

from tamil_edu_api import __version__
from tamil_edu_api.models import (
    HealthResponse,
    TranslateRequest,
    TranslateResponse,
    WordOut,
)

_VALID_BACKENDS = frozenset({"baseline", "aksharamukha", "indicxlit"})


def get_backend() -> str:
    """Read the active backend from env each call so tests + dev can override
    without restarting the app. Falls back to aksharamukha (real Tamil) if unset.
    """
    return os.environ.get("TRANSLITERATE_BACKEND", "aksharamukha").strip().lower()


def _allowed_origins() -> list[str]:
    return [
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
    backend = get_backend()
    if backend not in _VALID_BACKENDS:
        raise RuntimeError(
            f"TRANSLITERATE_BACKEND={backend!r} is invalid. Use one of {sorted(_VALID_BACKENDS)}."
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
    allow_origins=_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", backend=get_backend(), version=__version__)


@app.post("/translate", response_model=TranslateResponse, tags=["translate"])
async def translate_endpoint(req: TranslateRequest) -> TranslateResponse:
    backend = get_backend()
    start = time.perf_counter()
    try:
        backend_inst = _get(backend)
        words = backend_inst.transliterate_detailed(req.text, topk=req.topk)
    except TransliterationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:  # unknown backend or bad input
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    tamil = "".join(w.text for w in words)

    # Whole-string alternatives — best-effort, kept for v1 clients.
    alternatives: list[str] = []
    if req.topk > 1 and req.text:
        try:
            alternatives = backend_inst.alternatives(req.text, topk=req.topk)
        except (TransliterationError, ValueError):
            alternatives = [tamil]

    words_out = [
        WordOut(
            source=w.source,
            text=w.text,
            kind=str(w.kind),
            alternatives=w.alternatives,
        )
        for w in words
    ]

    duration_ms = int((time.perf_counter() - start) * 1000)
    return TranslateResponse(
        tamil=tamil,
        alternatives=alternatives,
        words=words_out,
        backend=backend,
        duration_ms=duration_ms,
    )
