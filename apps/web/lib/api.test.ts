import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, health, translate } from "./api";

const originalFetch = globalThis.fetch;

describe("translate()", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns the response body on 200", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        tamil: "வணக்கம்",
        alternatives: ["வணக்கம்"],
        words: [
          {
            source: "vanakkam",
            text: "வணக்கம்",
            kind: "tanglish",
            alternatives: ["வணக்கம்"],
          },
        ],
        backend: "indicxlit",
        duration_ms: 42,
      }),
    });

    const r = await translate("vanakkam", 1);
    expect(r.tamil).toBe("வணக்கம்");
    expect(r.backend).toBe("indicxlit");
    expect(r.duration_ms).toBe(42);
    expect(r.words).toHaveLength(1);
    expect(r.words[0].kind).toBe("tanglish");
  });

  it("posts JSON body with text + topk", async () => {
    const mock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        tamil: "x",
        alternatives: [],
        words: [],
        backend: "baseline",
        duration_ms: 0,
      }),
    });
    globalThis.fetch = mock as unknown as typeof fetch;

    await translate("hi", 5);

    const [, init] = mock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ text: "hi", topk: 5 });
    expect(init.headers["Content-Type"]).toBe("application/json");
  });

  it("throws ApiError with detail message on 4xx/5xx", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => ({ detail: "model not loaded" }),
    });

    await expect(translate("x")).rejects.toThrow(ApiError);
    await expect(translate("x")).rejects.toThrow("model not loaded");
  });

  it("falls back to HTTP status when error body is not JSON", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("not json");
      },
    });

    await expect(translate("x")).rejects.toThrow("HTTP 500");
  });
});

describe("health()", () => {
  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });
  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns health payload", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok", backend: "baseline", version: "0.0.1" }),
    });
    const r = await health();
    expect(r.status).toBe("ok");
  });

  it("throws on non-200", async () => {
    (globalThis.fetch as ReturnType<typeof vi.fn>).mockResolvedValue({ ok: false, status: 502 });
    await expect(health()).rejects.toThrow(ApiError);
  });
});
