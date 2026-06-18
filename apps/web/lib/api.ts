/**
 * Client for the tamil-edu-api FastAPI service.
 * The base URL comes from NEXT_PUBLIC_API_URL (defaults to localhost:8000 in dev).
 */

export type WordKind = "tanglish" | "english" | "punctuation" | "whitespace";

export type Word = {
  source: string;
  text: string;
  kind: WordKind;
  alternatives: string[];
};

export type TranslateResponse = {
  tamil: string;
  alternatives: string[];
  words: Word[];
  backend: string;
  duration_ms: number;
};

export type HealthResponse = {
  status: string;
  backend: string;
  version: string;
};

export type OcrLine = {
  text: string;
  confidence: number;
};

export type OcrResponse = {
  text: string;
  lines: OcrLine[];
  avg_confidence: number;
  backend: string;
  duration_ms: number;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Best-effort extraction of the FastAPI `{detail}` error message from a failed
 * response, falling back to the HTTP status when the body isn't JSON. */
async function errorDetail(r: Response): Promise<string> {
  try {
    const body = (await r.json()) as { detail?: string };
    if (body?.detail) return body.detail;
  } catch {
    // non-JSON error body (e.g. proxy HTML) — fall through to status
  }
  return `HTTP ${r.status}`;
}

export async function translate(text: string, topk = 3): Promise<TranslateResponse> {
  const r = await fetch(`${BASE_URL}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, topk }),
  });
  if (!r.ok) throw new ApiError(await errorDetail(r), r.status);
  return (await r.json()) as TranslateResponse;
}

/** OCR an image (printed Tamil / Tanglish) → extracted text + per-line confidence.
 * Note: do NOT set Content-Type — the browser adds the multipart boundary. */
export async function ocr(image: File): Promise<OcrResponse> {
  const form = new FormData();
  form.append("image", image);
  const r = await fetch(`${BASE_URL}/ocr`, { method: "POST", body: form });
  if (!r.ok) throw new ApiError(await errorDetail(r), r.status);
  return (await r.json()) as OcrResponse;
}

export async function health(): Promise<HealthResponse> {
  const r = await fetch(`${BASE_URL}/health`);
  if (!r.ok) throw new ApiError(`HTTP ${r.status}`, r.status);
  return (await r.json()) as HealthResponse;
}

export { ApiError, BASE_URL };
