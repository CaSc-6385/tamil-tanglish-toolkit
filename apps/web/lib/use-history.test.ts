// Tests for parseStored (pure function). The hook itself is exercised end-to-end
// via the page; this file proves the parser handles every malformed shape.

import { describe, expect, it } from "vitest";

import { __INTERNAL } from "./use-history";

const { parseStored, MAX_ENTRIES, STORAGE_KEY } = __INTERNAL;

describe("parseStored", () => {
  it("returns [] for null input", () => {
    expect(parseStored(null)).toEqual([]);
  });

  it("returns [] for empty string", () => {
    expect(parseStored("")).toEqual([]);
  });

  it("returns [] for invalid JSON", () => {
    expect(parseStored("{not json")).toEqual([]);
  });

  it("returns [] for non-array JSON", () => {
    expect(parseStored('{"foo":"bar"}')).toEqual([]);
  });

  it("parses a well-formed entry", () => {
    const entry = {
      id: "1-vanakkam",
      tanglish: "vanakkam",
      tamil: "வணக்கம்",
      backend: "indicxlit",
      timestamp: 1,
    };
    expect(parseStored(JSON.stringify([entry]))).toEqual([entry]);
  });

  it("drops malformed entries silently", () => {
    const good = {
      id: "1",
      tanglish: "hi",
      tamil: "hi",
      backend: "baseline",
      timestamp: 1,
    };
    const bad = [
      { id: 1 }, // wrong type for id
      { id: "x" }, // missing fields
      "not an object",
      null,
      good,
    ];
    expect(parseStored(JSON.stringify(bad))).toEqual([good]);
  });

  it(`caps to MAX_ENTRIES (${MAX_ENTRIES})`, () => {
    const many = Array.from({ length: 30 }, (_, i) => ({
      id: String(i),
      tanglish: `t${i}`,
      tamil: `T${i}`,
      backend: "baseline",
      timestamp: i,
    }));
    expect(parseStored(JSON.stringify(many))).toHaveLength(MAX_ENTRIES);
  });

  it("constants are sane", () => {
    expect(STORAGE_KEY).toMatch(/^aost-tamil:/);
    expect(MAX_ENTRIES).toBe(20);
  });
});
