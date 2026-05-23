"""Eval harness for Tanglish→Tamil conversion.

Usage:
    python -m eval.run --model baseline --set v1 --sample 10
    python -m eval.run --model baseline --set v1                  # full run
    python -m eval.run --compare baseline,gpt-4o-mini --domain conversation
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import jiwer
import sacrebleu

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO_ROOT / "data" / "golden"
REPORTS_DIR = REPO_ROOT / "eval" / "reports"


@dataclass(frozen=True)
class Pair:
    id: str
    tanglish: str
    expected_tamil: str
    domain: str
    difficulty: str
    reviewer: str = ""
    notes: str = ""


@dataclass
class Result:
    pair_id: str
    domain: str
    tanglish: str
    expected: str
    predicted: str

    @property
    def is_exact_match(self) -> bool:
        return self.predicted.strip() == self.expected.strip()


@dataclass
class Report:
    model: str
    set_name: str
    sample_size: int
    results: list[Result] = field(default_factory=list)

    def to_markdown(self) -> str:
        cer = self._cer()
        wer = self._wer()
        bleu = self._bleu()
        chrf = self._chrf()
        exact = sum(1 for r in self.results if r.is_exact_match) / max(len(self.results), 1)

        by_domain = self._metrics_by_domain()
        domain_rows = "\n".join(
            f"| {d} | {n} | {m['cer']:.2%} | {m['wer']:.2%} | {m['bleu']:.2f} | {m['chrf']:.2f} |"
            for d, (n, m) in sorted(by_domain.items())
        )

        worst = sorted(
            self.results, key=lambda r: jiwer.cer(r.expected, r.predicted), reverse=True
        )[:10]
        worst_rows = "\n".join(
            f"| {r.pair_id} | {r.domain} | `{r.tanglish[:40]}` | `{r.expected[:40]}` | `{r.predicted[:40]}` |"
            for r in worst
        )

        return f"""# Eval report — {self.model} on {self.set_name}

- **Run at**: {datetime.now(UTC).isoformat(timespec="seconds")}
- **Pairs evaluated**: {len(self.results)} (sampled from set `{self.set_name}`)
- **Model**: `{self.model}`

## Overall metrics

| Metric | Value | Target (S1) | Target (S2) |
|---|---|---|---|
| CER (Character Error Rate) | **{cer:.2%}** | ≤ 12% | ≤ 7% |
| WER (Word Error Rate) | **{wer:.2%}** | ≤ 25% | ≤ 18% |
| BLEU-4 | **{bleu:.2f}** | ≥ 60 | ≥ 72 |
| chrF | **{chrf:.2f}** | ≥ 75 | ≥ 82 |
| Exact match | **{exact:.2%}** | — | — |

## Per-domain breakdown

| Domain | N | CER | WER | BLEU | chrF |
|---|---|---|---|---|---|
{domain_rows}

## Worst 10 (highest CER)

| ID | Domain | Tanglish | Expected | Predicted |
|---|---|---|---|---|
{worst_rows}
"""

    def _cer(self) -> float:
        if not self.results:
            return 0.0
        return jiwer.cer(
            [r.expected for r in self.results],
            [r.predicted for r in self.results],
        )

    def _wer(self) -> float:
        if not self.results:
            return 0.0
        return jiwer.wer(
            [r.expected for r in self.results],
            [r.predicted for r in self.results],
        )

    def _bleu(self) -> float:
        if not self.results:
            return 0.0
        return sacrebleu.corpus_bleu(
            [r.predicted for r in self.results],
            [[r.expected for r in self.results]],
        ).score

    def _chrf(self) -> float:
        if not self.results:
            return 0.0
        return sacrebleu.corpus_chrf(
            [r.predicted for r in self.results],
            [[r.expected for r in self.results]],
        ).score

    def _metrics_by_domain(self) -> dict[str, tuple[int, dict[str, float]]]:
        out: dict[str, tuple[int, dict[str, float]]] = {}
        by_d: dict[str, list[Result]] = {}
        for r in self.results:
            by_d.setdefault(r.domain, []).append(r)
        for d, results in by_d.items():
            if not results:
                continue
            expected = [r.expected for r in results]
            predicted = [r.predicted for r in results]
            metrics = {
                "cer": jiwer.cer(expected, predicted),
                "wer": jiwer.wer(expected, predicted),
                "bleu": sacrebleu.corpus_bleu(predicted, [expected]).score,
                "chrf": sacrebleu.corpus_chrf(predicted, [expected]).score,
            }
            out[d] = (len(results), metrics)
        return out


class Model(Protocol):
    """A transliteration model. Real models implement this; baseline is a passthrough."""

    name: str

    def predict(self, tanglish: str) -> str: ...


class BaselineModel:
    """Identity baseline — returns input unchanged.

    Lets the harness run end-to-end before any real model is wired up.
    A real Tanglish→Tamil model will produce CER ~ 0; baseline produces CER ~ 1.0
    on Tamil-script targets, which is the expected starting line.
    """

    name = "baseline"

    def predict(self, tanglish: str) -> str:
        return tanglish


class IndicXlitModel:
    """Real IndicXlit Tamil model. Requires the `[indicxlit]` extra installed
    in the transliterate package. Slow to first-run (~1GB model load).

    Run:
        uv add --package tamil-edu-transliterate "ai4bharat-transliteration>=1.1.3"
        uv run python -m eval.run --model indicxlit --set v1

    **CURRENTLY BLOCKED**: ai4bharat-transliteration depends on fairseq, which
    has a `dataclass mutable default` bug that breaks on Python ≥ 3.11. Our
    project requires Python ≥ 3.11. Resolution requires either:
      (a) fairseq upstream fix (no recent activity), OR
      (b) lower our Python floor to 3.10 (loses StrEnum, etc.), OR
      (c) host IndicXlit as a separate service on Py 3.10.
    See docs/adr/0002-indicxlit-deferred.md.
    """

    name = "indicxlit"

    def __init__(self) -> None:
        from tamil_edu_transliterate import IndicXlitTransliterator

        self._impl = IndicXlitTransliterator()

    def predict(self, tanglish: str) -> str:
        return self._impl.transliterate(tanglish)


class AksharamukhaModel:
    """Rule-based Tamil transliteration via aksharamukha.

    Pure Python, no ML deps, works on any Python version. Quality is meaningfully
    lower than IndicXlit (rule tables can't capture Tanglish conventions like
    `nb` → `ண்ப` or doubled consonants), but unblocks end-to-end eval today.

    Treats input as ITRANS-like (closest scheme to common Tanglish).
    """

    name = "aksharamukha"

    def __init__(self) -> None:
        try:
            from aksharamukha import transliterate  # type: ignore[import-untyped]
        except ImportError as exc:
            raise SystemExit(
                "aksharamukha not installed. Install with: pip install aksharamukha"
            ) from exc
        self._fn = transliterate.process

    def predict(self, tanglish: str) -> str:
        # Tokenize so we only run rule-based transliteration on Tanglish tokens,
        # passing through English / punctuation / whitespace verbatim (S1-2 contract).
        from tamil_edu_transliterate import TokenKind, tokenize

        out: list[str] = []
        for tok in tokenize(tanglish):
            if tok.kind == TokenKind.TANGLISH:
                out.append(self._fn("IAST", "Tamil", tok.text))
            else:
                out.append(tok.text)
        return "".join(out)


MODELS: dict[str, Callable[[], Model]] = {
    "baseline": BaselineModel,
    "aksharamukha": AksharamukhaModel,
    "indicxlit": IndicXlitModel,
}


def load_pairs(set_name: str) -> list[Pair]:
    """Load the golden set. Falls back to a tiny built-in sample so the harness runs
    end-to-end even before S0-4 ships the full 1000-pair set.
    """
    csv_path = GOLDEN_DIR / f"{set_name}.csv"
    if csv_path.exists():
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [
                Pair(
                    id=row["id"],
                    tanglish=row["tanglish"],
                    expected_tamil=row["expected_tamil"],
                    domain=row["domain"],
                    difficulty=row.get("difficulty", "medium"),
                    reviewer=row.get("reviewer", ""),
                    notes=row.get("notes", ""),
                )
                for row in reader
            ]
    return _builtin_sample()


def _builtin_sample() -> list[Pair]:
    """10 hand-picked pairs covering the 5 domains. Replaced by data/golden/v1.csv (S0-4)."""
    return [
        Pair("smoke-001", "vanakkam", "வணக்கம்", "conversation", "easy"),
        Pair("smoke-002", "nandri", "நன்றி", "conversation", "easy"),
        Pair("smoke-003", "nalla iruka?", "நல்லா இருக்கா?", "conversation", "medium"),
        Pair("smoke-004", "Chennai", "சென்னை", "names", "easy"),
        Pair("smoke-005", "Karthik", "கார்த்திக்", "names", "medium"),
        Pair("smoke-006", "naan padikiren", "நான் படிக்கிறேன்", "school", "medium"),
        Pair("smoke-007", "rendu pasanga", "ரெண்டு பசங்க", "school", "medium"),
        Pair("smoke-008", "Modi vandhaaru", "மோடி வந்தாரு", "news", "medium"),
        Pair(
            "smoke-009",
            "send the message ku reply pannu",
            "send the message-கு reply பண்ணு",
            "code_switch",
            "hard",
        ),
        Pair(
            "smoke-010",
            "homework finish panniten",
            "homework finish பண்ணிட்டேன்",
            "code_switch",
            "hard",
        ),
    ]


def run(
    model_name: str,
    set_name: str,
    sample: int | None,
    domain: str | None,
) -> Report:
    if model_name not in MODELS:
        raise SystemExit(f"Unknown model '{model_name}'. Available: {sorted(MODELS)}")
    model = MODELS[model_name]()
    pairs = load_pairs(set_name)
    if domain:
        pairs = [p for p in pairs if p.domain == domain]
    if sample is not None:
        pairs = pairs[:sample]
    if not pairs:
        raise SystemExit(f"No pairs matched (set={set_name}, domain={domain}).")

    results = [
        Result(
            pair_id=p.id,
            domain=p.domain,
            tanglish=p.tanglish,
            expected=p.expected_tamil,
            predicted=model.predict(p.tanglish),
        )
        for p in pairs
    ]
    return Report(model=model_name, set_name=set_name, sample_size=len(results), results=results)


def write_report(report: Report) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y-%m-%d-%H%M%S")
    path = REPORTS_DIR / f"{ts}-{report.model}-{report.set_name}.md"
    path.write_text(report.to_markdown(), encoding="utf-8")
    return path


def main(argv: Iterable[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="eval.run", description=__doc__)
    p.add_argument("--model", default="baseline", help=f"Available: {sorted(MODELS)}")
    p.add_argument(
        "--set", dest="set_name", default="v1", help="Golden set name (CSV in data/golden/)"
    )
    p.add_argument("--sample", type=int, default=None, help="Limit pairs (None = all)")
    p.add_argument("--domain", default=None, help="Filter to one domain")
    p.add_argument("--no-report", action="store_true", help="Skip writing markdown report")
    p.add_argument(
        "--json", dest="emit_json", action="store_true", help="Emit JSON summary to stdout"
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    report = run(args.model, args.set_name, args.sample, args.domain)

    summary = {
        "model": report.model,
        "set": report.set_name,
        "n": len(report.results),
        "cer": report._cer(),
        "wer": report._wer(),
        "bleu": report._bleu(),
        "chrf": report._chrf(),
    }

    if not args.no_report:
        path = write_report(report)
        # Show repo-relative path when possible; otherwise the absolute path.
        try:
            shown = path.relative_to(REPO_ROOT)
        except ValueError:
            shown = path
        print(f"Report: {shown}", file=sys.stderr)

    if args.emit_json:
        print(json.dumps(summary, indent=2))
    else:
        print(
            f"{report.model} on {report.set_name} (n={summary['n']}): "
            f"CER={summary['cer']:.2%}  WER={summary['wer']:.2%}  "
            f"BLEU={summary['bleu']:.2f}  chrF={summary['chrf']:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
