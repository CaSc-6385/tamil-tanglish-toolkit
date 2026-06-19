"use client";

import { useEffect, useState } from "react";

import { analyze, ocr, type AnalyzeResponse, type WordAnalysis } from "@/lib/api";
import { capture, initPostHog } from "@/lib/posthog";
import { useHistory } from "@/lib/use-history";

const SAMPLES = ["vanakkam nanba", "naan periya naai paarthen", "enaku pasikuthu", "nalla iruka?"];

// Color per part of speech (full literal classes so Tailwind keeps them).
const POS_STYLE: Record<string, string> = {
  noun: "bg-sky-500/15 text-sky-300 border-sky-400/30",
  verb: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
  adjective: "bg-violet-500/15 text-violet-300 border-violet-400/30",
  adverb: "bg-pink-500/15 text-pink-300 border-pink-400/30",
  pronoun: "bg-teal-500/15 text-teal-300 border-teal-400/30",
  postposition: "bg-amber-500/15 text-amber-300 border-amber-400/30",
  conjunction: "bg-slate-500/20 text-slate-300 border-slate-400/30",
  numeral: "bg-orange-500/15 text-orange-300 border-orange-400/30",
  particle: "bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-400/30",
  other: "bg-white/5 text-slate-300 border-white/15",
};
const posStyle = (p: string) => POS_STYLE[p] ?? POS_STYLE.other;

export default function HomePage() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrNote, setOcrNote] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { history, add: addHistory, remove: removeHistory, clear: clearHistory } = useHistory();

  useEffect(() => {
    initPostHog();
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    const tStart = performance.now();
    capture("analyze.requested", { length: input.length });
    try {
      const r = await analyze(input);
      setResult(r);
      addHistory({ tanglish: input, tamil: r.tamil, backend: r.translate_model });
      capture("analyze.succeeded", {
        input_length: input.length,
        output_length: r.tamil.length,
        word_count: r.words.length,
        duration_ms: Math.round(performance.now() - tStart),
        server_duration_ms: r.duration_ms,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg);
      setResult(null);
      capture("analyze.error", { message_class: msg.slice(0, 80), input_length: input.length });
    } finally {
      setLoading(false);
    }
  }

  async function onCopy() {
    if (!result) return;
    await navigator.clipboard.writeText(result.tamil);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

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
    if (typeof window !== "undefined") window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const uniquePos = result ? [...new Set(result.words.map((w) => w.pos))] : [];

  return (
    <main className="mx-auto max-w-2xl px-5 py-12 sm:py-16">
      <header className="mb-8 animate-fade-up">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-aost-300">
          <span className="h-2 w-2 animate-pulse-dot rounded-full bg-aost-400" aria-hidden="true" />
          Translate · understand · free &amp; local
        </span>
        <h1 className="gradient-text mt-4 text-4xl font-extrabold tracking-tight sm:text-5xl">
          AOST Tamil
        </h1>
        <p className="mt-3 text-lg text-slate-400">
          Type Tanglish → get Tamil, with a word-by-word picture breakdown.{" "}
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
          placeholder="e.g. naan periya naai paarthen"
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
          {loading ? "Translating & explaining…" : "Translate & explain"}
        </button>
        {loading && (
          <p className="mt-2 text-center text-xs text-slate-500">
            Sarvam is translating, then gemma2 is breaking it down — this can take ~15s.
          </p>
        )}
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
          <p className="font-semibold text-red-300">Something went wrong</p>
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
            <span className="text-xs text-slate-500">{result.duration_ms} ms</span>
          </div>

          <div className="rounded-2xl border border-white/10 bg-black/30 px-5 py-5">
            <p
              className="tamil-glow animate-pop-in font-tamil text-kid-lg leading-relaxed text-white"
              lang="ta"
            >
              {result.tamil || "—"}
            </p>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-3">
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
            <p className="text-xs text-slate-500">
              Understood &amp; translated locally · breakdown by {result.analyze_model || "gemma2"}
            </p>
          </div>

          {result.words.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-3 text-sm font-semibold text-slate-200">Sentence breakdown 🧩</h3>
              <div className="flex flex-wrap gap-2.5">
                {result.words.map((w, i) => (
                  <WordCard key={i} w={w} />
                ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {uniquePos.map((p) => (
                  <span
                    key={p}
                    className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${posStyle(p)}`}
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {history.length > 0 && (
        <section
          aria-labelledby="history-heading"
          className="glass mb-8 animate-fade-up rounded-3xl p-5 sm:p-6"
        >
          <div className="mb-3 flex items-baseline justify-between">
            <h2 id="history-heading" className="text-sm font-semibold text-slate-200">
              Recent
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
          . Powered by free local models via{" "}
          <a className="text-aost-300 underline-offset-2 hover:underline" href="https://ollama.com">
            Ollama
          </a>
          .
        </p>
      </footer>
    </main>
  );
}

/** A single word tile: emoji picture + Tamil + English gloss + colour-coded POS. */
function WordCard({ w }: { w: WordAnalysis }) {
  return (
    <div className="flex min-w-[88px] max-w-[140px] flex-col items-center gap-1 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-center transition hover:-translate-y-0.5 hover:bg-white/10">
      <div className="flex h-9 items-center justify-center text-3xl" aria-hidden="true">
        {w.emoji || <span className="text-base text-slate-600">·</span>}
      </div>
      <div className="font-tamil text-xl leading-tight text-white" lang="ta">
        {w.tamil}
      </div>
      {w.gloss && <div className="text-xs text-slate-400">{w.gloss}</div>}
      <span
        className={`mt-0.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${posStyle(w.pos)}`}
      >
        {w.pos}
      </span>
    </div>
  );
}
