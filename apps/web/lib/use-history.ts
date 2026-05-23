"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "aost-tamil:history:v1";
const MAX_ENTRIES = 20;

export type HistoryEntry = {
  /** Stable id derived from timestamp + tanglish */
  id: string;
  tanglish: string;
  tamil: string;
  backend: string;
  /** Epoch ms */
  timestamp: number;
};

type RawEntry = Partial<HistoryEntry>;

/** Safe parse: drops malformed entries silently. */
function parseStored(raw: string | null): HistoryEntry[] {
  if (!raw) return [];
  try {
    const data = JSON.parse(raw) as unknown;
    if (!Array.isArray(data)) return [];
    return (data as RawEntry[])
      .filter(
        (e): e is HistoryEntry =>
          typeof e?.id === "string" &&
          typeof e?.tanglish === "string" &&
          typeof e?.tamil === "string" &&
          typeof e?.backend === "string" &&
          typeof e?.timestamp === "number",
      )
      .slice(0, MAX_ENTRIES);
  } catch {
    return [];
  }
}

/**
 * Persist last 20 translations in localStorage. COPPA-safe: no accounts,
 * no PII collected; data lives only on the device.
 *
 * Usage:
 *   const { history, add, remove, clear } = useHistory();
 */
export function useHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from localStorage after mount (SSR-safe).
  useEffect(() => {
    if (typeof window === "undefined") return;
    setHistory(parseStored(window.localStorage.getItem(STORAGE_KEY)));
    setHydrated(true);
  }, []);

  // Persist on change (skip the initial hydration write).
  useEffect(() => {
    if (!hydrated || typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  }, [history, hydrated]);

  const add = useCallback((entry: Omit<HistoryEntry, "id" | "timestamp">) => {
    const ts = Date.now();
    const next: HistoryEntry = { ...entry, id: `${ts}-${entry.tanglish}`, timestamp: ts };
    setHistory((prev) => {
      // De-dupe by tanglish — most recent moves to front, others kept in order
      const filtered = prev.filter((e) => e.tanglish !== entry.tanglish);
      return [next, ...filtered].slice(0, MAX_ENTRIES);
    });
  }, []);

  const remove = useCallback((id: string) => {
    setHistory((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const clear = useCallback(() => {
    setHistory([]);
  }, []);

  return { history, add, remove, clear, hydrated };
}

// Exported for tests
export const __INTERNAL = { STORAGE_KEY, MAX_ENTRIES, parseStored };
