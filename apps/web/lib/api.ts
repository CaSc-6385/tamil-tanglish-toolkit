/**
 * Client for the tamil-edu-api FastAPI service.
 * The base URL comes from NEXT_PUBLIC_API_URL (defaults to localhost:8000 in dev).
 */

export type TranslateResponse = {
  tamil: string;
  alternatives: string[];
  backend: string;
  duration_ms: number;
};

export type HealthResponse = {
  status: string;
  backend: string;
  version: string;
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

export async function translate(text: string, topk = 3): Promise<TranslateResponse> {
  const r = await fetch(`${BASE_URL}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, topk }),
  });
  if (!r.ok) {
    let detail = `HTTP ${r.status}`;
    try {
      const body = (await r.json()) as { detail?: string };
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore parse error
    }
    throw new ApiError(detail, r.status);
  }
  return (await r.json()) as TranslateResponse;
}

export async function health(): Promise<HealthResponse> {
  const r = await fetch(`${BASE_URL}/health`);
  if (!r.ok) throw new ApiError(`HTTP ${r.status}`, r.status);
  return (await r.json()) as HealthResponse;
}

export { ApiError, BASE_URL };
