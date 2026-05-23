"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=0, max_length=2000, description="Tanglish input")
    topk: int = Field(default=3, ge=1, le=10, description="Number of alternatives to return")


class TranslateResponse(BaseModel):
    tamil: str = Field(..., description="Best Tamil transliteration")
    alternatives: list[str] = Field(
        default_factory=list, description="Top-K candidates, best first"
    )
    backend: str = Field(..., description="Backend used (baseline / indicxlit)")
    duration_ms: int = Field(..., ge=0, description="Server-side processing time in milliseconds")


class HealthResponse(BaseModel):
    status: str
    backend: str
    version: str
