"use client";

import { useState } from "react";

import { translate, type TranslateResponse, type Word } from "@/lib/api";
import { useHistory } from "@/lib/use-history";

const SAMPLES = [
  "vanakkam nanba",
  "nalla iruka?",
  "naan padikiren",
  "send the message reply pannu",
];

export default function HomePage() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<TranslateResponse | null>(null);
  // overrides[wordIndex] = chosen alternative text (per-word swap state)
  const [overrides, setOverrides] = useState<Record<number, string>>({});
  // openIdx = which word's popover is currently open
  const [openIdx, setOpenIdx] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { history, add: addHistory, remove: removeHistory, clear: clearHistory } = useHistory();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setOverrides({});
    setOpenIdx(null);
    try {
      const r = await translate(input, 3);
      setResult(r);
      addHistory({ tanglish: input, tamil: r.tamil, backend: r.backend });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg);
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function currentTamil(): string {
    if (!result) return "";
    return result.words.map((w, i) => overrides[i] ?? w.text).join("");
  }

  async function onCopy() {
    if (!result) return;
    await navigator.clipboard.writeText(currentTamil());
  }

  function loadFromHistory(tanglish: string) {
    setInput(tanglish);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  function pickAlternative(wordIdx: number, alt: string) {
    setOverrides((prev) => ({ ...prev, [wordIdx]: alt }));
    setOpenIdx(null);
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <header className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-aost-700">AOST Tamil</h1>
        <p className="mt-2 text-lg text-aost-900/80">
          Type Tanglish, get Tamil. <span className="font-tamil">வணக்கம்! 🌸</span>
        </p>
      </header>

      <form onSubmit={onSubmit} className="mb-6">
        <label htmlFor="tanglish" className="mb-2 block text-base font-medium">
          Type in Tanglish:
        </label>
        <textarea
          id="tanglish"
          name="tanglish"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. vanakkam nanba"
          rows={3}
          className="w-full rounded-2xl border-2 border-aost-300 bg-white px-4 py-3 text-kid placeholder:text-aost-400 focus:border-aost-500"
          aria-describedby="tanglish-help"
        />
        <p id="tanglish-help" className="mt-1 text-sm text-aost-900/60">
          Up to 2000 characters. Try a sample below to get started.
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          {SAMPLES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setInput(s)}
              className="rounded-full border border-aost-300 bg-aost-100 px-3 py-1 text-sm text-aost-700 hover:bg-aost-200"
            >
              {s}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="mt-4 w-full rounded-2xl bg-aost-500 px-5 py-3 text-lg font-semibold text-white shadow-sm hover:bg-aost-600 disabled:cursor-not-allowed disabled:bg-aost-300"
        >
          {loading ? "Translating…" : "Translate to Tamil"}
        </button>
      </form>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-xl border-2 border-red-300 bg-red-50 px-4 py-3 text-red-900"
        >
          <p className="font-medium">Could not translate</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {result && (
        <section aria-labelledby="output-heading" className="mb-8">
          <div className="flex items-baseline justify-between">
            <h2 id="output-heading" className="text-lg font-medium text-aost-900">
              Tamil:
            </h2>
            <span className="text-xs text-aost-900/50">
              {result.backend} · {result.duration_ms} ms
            </span>
          </div>

          <div className="mt-2 rounded-2xl border-2 border-aost-400 bg-aost-50 px-5 py-4">
            <p className="font-tamil text-kid-lg leading-relaxed" lang="ta">
              {result.words.map((w, i) => (
                <WordChip
                  key={i}
                  word={w}
                  chosen={overrides[i] ?? w.text}
                  isOpen={openIdx === i}
                  onToggle={() => setOpenIdx(openIdx === i ? null : i)}
                  onPick={(alt) => pickAlternative(i, alt)}
                />
              ))}
            </p>
          </div>

          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={onCopy}
              className="rounded-xl border border-aost-400 bg-white px-4 py-2 text-sm font-medium text-aost-700 hover:bg-aost-100"
            >
              Copy
            </button>
            <p className="self-center text-sm text-aost-900/60">
              Tap any word with alternatives to swap.
            </p>
          </div>
        </section>
      )}

      {history.length > 0 && (
        <section aria-labelledby="history-heading" className="mb-10">
          <div className="mb-3 flex items-baseline justify-between">
            <h2 id="history-heading" className="text-lg font-medium text-aost-900">
              Recent translations
            </h2>
            <button
              type="button"
              onClick={clearHistory}
              className="text-sm text-aost-700 underline hover:text-aost-900"
              aria-label={`Clear all ${history.length} history items`}
            >
              Clear all
            </button>
          </div>
          <ul className="space-y-2">
            {history.map((h) => (
              <li
                key={h.id}
                className="flex items-center justify-between rounded-xl border border-aost-200 bg-white px-3 py-2"
              >
                <button
                  type="button"
                  onClick={() => loadFromHistory(h.tanglish)}
                  className="min-w-0 flex-1 truncate text-left"
                  aria-label={`Reuse ${h.tanglish}`}
                >
                  <span className="block truncate text-sm text-aost-900/70">{h.tanglish}</span>
                  <span className="font-tamil block truncate" lang="ta">
                    {h.tamil}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => removeHistory(h.id)}
                  className="ml-3 text-aost-900/40 hover:text-red-600"
                  aria-label={`Remove ${h.tanglish}`}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-aost-900/50">
            Saved only on your device. No account, no upload.
          </p>
        </section>
      )}

      <footer className="mt-12 border-t border-aost-200 pt-6 text-center text-sm text-aost-900/60">
        <p>
          Part of{" "}
          <a className="underline" href="https://www.academyofsmartthinkers.com/">
            Academy of Smart Thinkers
          </a>
          . Open source on{" "}
          <a className="underline" href="https://github.com/chandralabs/tamil-edu-toolkit">
            GitHub
          </a>
          .
        </p>
        <p className="mt-1">
          Engine:{" "}
          <a className="underline" href="https://github.com/chandralabs/tamil-llama">
            chandralabs/tamil-llama
          </a>{" "}
          + IndicXlit.
        </p>
      </footer>
    </main>
  );
}

/**
 * Inline word with alternative-picker popover.
 *
 * - Whitespace tokens render as-is (preserving spacing) with no interaction.
 * - English / punctuation tokens render plain (no alternatives).
 * - Tanglish tokens with >1 alternatives render as a button → popover.
 */
function WordChip({
  word,
  chosen,
  isOpen,
  onToggle,
  onPick,
}: {
  word: Word;
  chosen: string;
  isOpen: boolean;
  onToggle: () => void;
  onPick: (alt: string) => void;
}) {
  if (word.kind === "whitespace") {
    return <span>{chosen}</span>;
  }
  if (word.kind !== "tanglish" || word.alternatives.length <= 1) {
    return <span>{chosen}</span>;
  }
  return (
    <span className="relative inline-block">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-label={`${chosen} — ${word.alternatives.length} alternatives`}
        className="rounded-md border-b-2 border-dotted border-aost-500 hover:bg-aost-100 focus:bg-aost-100"
      >
        {chosen}
      </button>
      {isOpen && (
        <span
          role="dialog"
          aria-label={`Alternatives for ${chosen}`}
          className="absolute left-0 top-full z-10 mt-1 min-w-[8rem] rounded-xl border-2 border-aost-400 bg-white p-2 text-base shadow-lg"
        >
          {word.alternatives.map((alt) => (
            <button
              key={alt}
              type="button"
              onClick={() => onPick(alt)}
              className={`block w-full rounded-md px-2 py-1 text-left font-tamil hover:bg-aost-50 ${
                alt === chosen ? "bg-aost-100 font-semibold" : ""
              }`}
              lang="ta"
            >
              {alt}
            </button>
          ))}
        </span>
      )}
    </span>
  );
}
