"use client";

import { useEffect, useState } from "react";

import { ocr, translate, type TranslateResponse, type Word } from "@/lib/api";
import { capture, initPostHog } from "@/lib/posthog";
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
  // OCR (image → text) state
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrNote, setOcrNote] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { history, add: addHistory, remove: removeHistory, clear: clearHistory } = useHistory();

  // Initialize PostHog once on mount (no-op if NEXT_PUBLIC_POSTHOG_KEY unset).
  useEffect(() => {
    initPostHog();
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setOverrides({});
    setOpenIdx(null);
    const tStart = performance.now();
    capture("translate.requested", { length: input.length });
    try {
      const r = await translate(input, 3);
      setResult(r);
      addHistory({ tanglish: input, tamil: r.tamil, backend: r.backend });
      capture("translate.succeeded", {
        backend: r.backend,
        input_length: input.length,
        output_length: r.tamil.length,
        duration_ms: Math.round(performance.now() - tStart),
        server_duration_ms: r.duration_ms,
        word_count: r.words.length,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg);
      setResult(null);
      capture("translate.error", {
        message_class: msg.slice(0, 80),
        input_length: input.length,
      });
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
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  // Read text from an uploaded image (printed Tamil / Tanglish) and drop it into
  // the input so the user can review before translating.
  async function onImageSelected(file: File | null | undefined) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setOcrNote("Please choose an image file.");
      return;
    }
    setOcrLoading(true);
    setOcrNote(null);
    setError(null);
    const tStart = performance.now();
    capture("ocr.requested", { file_size: file.size, file_type: file.type });
    try {
      const res = await ocr(file);
      const extracted = res.text.trim();
      if (!extracted) {
        setOcrNote("No readable text found in that image.");
      } else {
        setInput((prev) => (prev.trim() ? `${prev.trim()} ${extracted}` : extracted));
        setOcrNote(
          `Extracted ${res.lines.length} line(s) · ${Math.round(res.avg_confidence * 100)}% confidence`,
        );
      }
      capture("ocr.succeeded", {
        extracted_length: extracted.length,
        file_size: file.size,
        duration_ms: Math.round(performance.now() - tStart),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Could not read that image";
      setOcrNote(msg);
      capture("ocr.error", { message_class: msg.slice(0, 80), file_size: file.size });
    } finally {
      setOcrLoading(false);
    }
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
    <main className="mx-auto max-w-2xl px-5 py-12 sm:py-16">
      <header className="mb-8 animate-fade-up">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-aost-300">
          <span className="h-2 w-2 animate-pulse-dot rounded-full bg-aost-400" aria-hidden="true" />
          Tanglish → Tamil · free &amp; local
        </span>
        <h1 className="gradient-text mt-4 text-4xl font-extrabold tracking-tight sm:text-5xl">
          AOST Tamil
        </h1>
        <p className="mt-3 text-lg text-slate-400">
          Type Tanglish, get correct Tamil.{" "}
          <span className="font-tamil text-slate-200">வணக்கம்! 🌸</span>
        </p>
      </header>

      <form
        onSubmit={onSubmit}
        className="glass mb-5 animate-fade-up rounded-3xl p-5 sm:p-6"
        style={{ animationDelay: "0.07s" }}
      >
        <label htmlFor="tanglish" className="mb-2 block text-sm font-semibold text-slate-200">
          Type in Tanglish
        </label>
        <textarea
          id="tanglish"
          name="tanglish"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. vanakkam nanba"
          rows={3}
          maxLength={2000}
          className="w-full resize-y rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-kid text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-aost-400/70 focus:bg-white/[0.07] focus:ring-4 focus:ring-aost-400/15"
          aria-describedby="tanglish-help"
        />
        <p id="tanglish-help" className="mt-1.5 text-xs text-slate-500">
          Up to 2000 characters. Try a sample below to get started.
        </p>

        <div className="mt-3 flex flex-wrap gap-2">
          {SAMPLES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setInput(s)}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-300 transition hover:border-aost-400/50 hover:bg-white/10 hover:text-white"
            >
              {s}
            </button>
          ))}
        </div>

        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="shimmer relative mt-5 flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl bg-gradient-to-r from-aost-400 via-orange-500 to-aost-500 px-5 py-3.5 text-lg font-bold text-ink-900 shadow-[0_14px_30px_-10px_rgba(247,174,53,0.6)] transition hover:-translate-y-0.5 hover:shadow-[0_20px_44px_-12px_rgba(247,174,53,0.75)] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0"
        >
          {loading && (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-ink-900/40 border-t-ink-900" />
          )}
          {loading ? "Translating…" : "Translate to Tamil"}
        </button>
      </form>

      <section
        aria-labelledby="ocr-heading"
        className="glass mb-5 animate-fade-up rounded-3xl p-5 sm:p-6"
        style={{ animationDelay: "0.14s" }}
      >
        <h2 id="ocr-heading" className="mb-3 text-sm font-semibold text-slate-200">
          Or read text from an image
        </h2>
        <label
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            onImageSelected(e.dataTransfer.files?.[0]);
          }}
          className="group flex cursor-pointer flex-col items-center justify-center gap-1 rounded-2xl border-2 border-dashed border-white/15 bg-white/[0.03] px-4 py-7 text-center transition hover:border-aost-400/60 hover:bg-white/5 focus-within:border-aost-400/60"
        >
          <input
            type="file"
            accept="image/*"
            className="sr-only"
            disabled={ocrLoading}
            onChange={(e) => onImageSelected(e.target.files?.[0])}
          />
          <span className="text-3xl transition-transform group-hover:scale-110" aria-hidden="true">
            🖼️
          </span>
          <span className="text-sm font-medium text-slate-200">
            {ocrLoading ? "Reading image…" : "Drop an image or tap to choose"}
          </span>
          <span className="text-xs text-slate-500">
            PNG, JPG, or WEBP · printed Tamil or Tanglish
          </span>
        </label>
        {ocrNote && (
          <p role="status" aria-live="polite" className="mt-2 text-sm text-aost-300">
            {ocrNote}
          </p>
        )}
      </section>

      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="mb-5 animate-fade-up rounded-2xl border border-red-500/30 bg-red-500/10 p-4"
        >
          <p className="font-semibold text-red-300">Could not translate</p>
          <p className="mt-0.5 text-sm text-red-200/80">{error}</p>
        </div>
      )}

      {result && (
        <section
          aria-labelledby="output-heading"
          className="glass mb-5 animate-fade-up rounded-3xl p-5 sm:p-6"
        >
          <div className="mb-3 flex items-baseline justify-between">
            <h2
              id="output-heading"
              className="text-sm font-semibold uppercase tracking-wider text-slate-400"
            >
              Tamil
            </h2>
            <span className="text-xs text-slate-500">
              {result.backend} · {result.duration_ms} ms
            </span>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/30 px-5 py-5">
            <p
              className="tamil-glow animate-pop-in font-tamil text-kid-lg leading-relaxed text-white"
              lang="ta"
            >
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

          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={onCopy}
              aria-label="Copy Tamil text to clipboard"
              className={`rounded-xl border px-4 py-2 text-sm font-medium transition ${
                copied
                  ? "border-teal-400/40 bg-teal-400/15 text-teal-200"
                  : "border-white/10 bg-white/5 text-teal-300 hover:bg-white/10"
              }`}
            >
              {copied ? "Copied!" : "Copy"}
            </button>
            <p className="text-sm text-slate-500">Tap any underlined word to swap.</p>
          </div>
        </section>
      )}

      {history.length > 0 && (
        <section
          aria-labelledby="history-heading"
          className="glass mb-8 animate-fade-up rounded-3xl p-5 sm:p-6"
        >
          <div className="mb-3 flex items-baseline justify-between">
            <h2 id="history-heading" className="text-sm font-semibold text-slate-200">
              Recent translations
            </h2>
            <button
              type="button"
              onClick={clearHistory}
              className="text-sm text-slate-400 underline-offset-2 transition hover:text-white hover:underline"
              aria-label={`Clear all ${history.length} history items`}
            >
              Clear all
            </button>
          </div>
          <ul className="space-y-2">
            {history.map((h) => (
              <li
                key={h.id}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2.5 transition hover:bg-white/10"
              >
                <button
                  type="button"
                  onClick={() => loadFromHistory(h.tanglish)}
                  className="min-w-0 flex-1 truncate text-left"
                  aria-label={`Reuse ${h.tanglish}`}
                >
                  <span className="block truncate text-sm text-slate-500">{h.tanglish}</span>
                  <span className="block truncate font-tamil text-slate-100" lang="ta">
                    {h.tamil}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => removeHistory(h.id)}
                  className="ml-3 text-slate-500 transition hover:text-red-400"
                  aria-label={`Remove ${h.tanglish}`}
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-slate-600">
            Saved only on your device. No account, no upload.
          </p>
        </section>
      )}

      <footer className="mt-10 border-t border-white/10 pt-6 text-center text-sm text-slate-500">
        <p>
          Part of{" "}
          <a
            className="text-aost-300 underline-offset-2 hover:underline"
            href="https://www.academyofsmartthinkers.com/"
          >
            Academy of Smart Thinkers
          </a>
          . Open source on{" "}
          <a
            className="text-aost-300 underline-offset-2 hover:underline"
            href="https://github.com/chandralabs/tamil-edu-toolkit"
          >
            GitHub
          </a>
          .
        </p>
        <p className="mt-1">
          Engine:{" "}
          <a
            className="text-aost-300 underline-offset-2 hover:underline"
            href="https://github.com/chandralabs/tamil-llama"
          >
            chandralabs/tamil-llama
          </a>{" "}
          via Ollama.
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
        aria-haspopup="menu"
        aria-label={`${chosen} — ${word.alternatives.length} alternatives`}
        lang="ta"
        className="rounded-md border-b-2 border-dotted border-aost-400/70 px-0.5 transition hover:bg-white/10 focus:bg-white/10"
      >
        {chosen}
      </button>
      {isOpen && (
        <span
          role="menu"
          aria-label={`Alternatives for ${chosen}`}
          className="absolute left-0 top-full z-10 mt-1 min-w-[9rem] animate-pop-in rounded-xl border border-white/10 bg-ink-700/95 p-1.5 text-base shadow-2xl backdrop-blur"
        >
          {word.alternatives.map((alt) => (
            <button
              key={alt}
              type="button"
              role="menuitem"
              onClick={() => onPick(alt)}
              className={`block w-full rounded-lg px-2.5 py-1.5 text-left font-tamil transition hover:bg-white/10 ${
                alt === chosen ? "bg-aost-400/15 font-semibold text-aost-200" : "text-slate-200"
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
