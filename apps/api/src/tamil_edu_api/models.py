"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=0, max_length=2000, description="Tanglish input")
    topk: int = Field(default=3, ge=1, le=10, description="Number of alternatives to return")


class WordOut(BaseModel):
    """One token of the output. Mirrors `tamil_edu_transliterate.Word`."""

    source: str = Field(..., description="The original Tanglish/English/punct/whitespace token")
    text: str = Field(..., description="The chosen Tamil text for this token (top-1)")
    kind: str = Field(..., description="tanglish / english / punctuation / whitespace")
    alternatives: list[str] = Field(
        default_factory=list,
        description="Top-K candidate transliterations for this token (empty for non-Tanglish)",
    )


class TranslateResponse(BaseModel):
    tamil: str = Field(..., description="Best Tamil transliteration (join of words[*].text)")
    alternatives: list[str] = Field(
        default_factory=list,
        description="Top-K WHOLE-STRING candidates, best first. Kept for back-compat with v1 clients.",
    )
    words: list[WordOut] = Field(
        default_factory=list,
        description="Per-token output with per-word alternatives. Use this for per-word UI.",
    )
    backend: str = Field(..., description="Backend used (baseline / indicxlit)")
    duration_ms: int = Field(..., ge=0, description="Server-side processing time in milliseconds")


class OcrLineOut(BaseModel):
    """One detected line of text. Mirrors `tamil_edu_ocr.OcrLine`."""

    text: str = Field(..., description="The recognised text for this line")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Mean confidence in [0, 1]")


class OcrResponse(BaseModel):
    text: str = Field(..., description="All recognised text, lines joined by spaces")
    lines: list[OcrLineOut] = Field(
        default_factory=list, description="Per-line text + confidence, in reading order"
    )
    avg_confidence: float = Field(..., ge=0.0, le=1.0, description="Mean confidence across lines")
    backend: str = Field(..., description="OCR backend used (baseline / tesseract)")
    duration_ms: int = Field(..., ge=0, description="Server-side processing time in milliseconds")


class HealthResponse(BaseModel):
    status: str
    backend: str
    version: str
