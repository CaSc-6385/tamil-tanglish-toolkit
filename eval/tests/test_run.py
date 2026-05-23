"""Tests for the eval harness skeleton."""

from __future__ import annotations

from pathlib import Path

import pytest

from eval.run import (
    BaselineModel,
    Pair,
    Result,
    _builtin_sample,
    load_pairs,
    main,
    run,
)


def test_baseline_returns_input_unchanged() -> None:
    m = BaselineModel()
    assert m.predict("vanakkam") == "vanakkam"
    assert m.name == "baseline"


def test_builtin_sample_covers_all_five_domains() -> None:
    sample = _builtin_sample()
    domains = {p.domain for p in sample}
    assert domains == {"conversation", "names", "school", "news", "code_switch"}
    assert len(sample) == 10


def test_load_pairs_falls_back_to_builtin_when_csv_missing() -> None:
    pairs = load_pairs("nonexistent-set-name")
    assert pairs == _builtin_sample()


def test_load_pairs_reads_csv_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import eval.run as runmod

    csv_path = tmp_path / "tinyset.csv"
    csv_path.write_text(
        "id,tanglish,expected_tamil,domain,difficulty,reviewer,notes\n"
        "t-1,hello,வணக்கம்,conversation,easy,sc,\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(runmod, "GOLDEN_DIR", tmp_path)
    pairs = runmod.load_pairs("tinyset")
    assert len(pairs) == 1
    assert pairs[0].tanglish == "hello"
    assert pairs[0].expected_tamil == "வணக்கம்"


def test_run_with_baseline_against_builtin_produces_high_cer() -> None:
    """Baseline returns input unchanged → CER vs. Tamil target should be ~ 1.0."""
    report = run("baseline", "smoke", sample=None, domain=None)
    assert len(report.results) == 10
    assert report._cer() > 0.9  # almost every character is wrong


def test_run_unknown_model_exits() -> None:
    with pytest.raises(SystemExit):
        run("does-not-exist", "smoke", sample=None, domain=None)


def test_run_filters_by_domain() -> None:
    report = run("baseline", "smoke", sample=None, domain="conversation")
    assert all(r.domain == "conversation" for r in report.results)
    assert len(report.results) >= 3  # 3 conversation pairs in builtin


def test_run_respects_sample_limit() -> None:
    report = run("baseline", "smoke", sample=3, domain=None)
    assert len(report.results) == 3


def test_report_markdown_contains_all_sections() -> None:
    report = run("baseline", "smoke", sample=None, domain=None)
    md = report.to_markdown()
    for section in [
        "# Eval report",
        "## Overall metrics",
        "## Per-domain breakdown",
        "## Worst 10 (highest CER)",
        "CER (Character Error Rate)",
        "BLEU-4",
        "chrF",
    ]:
        assert section in md, f"missing section: {section}"


def test_result_exact_match() -> None:
    r1 = Result("a", "d", "hi", "வணக்கம்", "வணக்கம்")
    r2 = Result("b", "d", "hi", "வணக்கம்", "வணக்கம் ")  # whitespace ignored
    r3 = Result("c", "d", "hi", "வணக்கம்", "Hello")
    assert r1.is_exact_match
    assert r2.is_exact_match
    assert not r3.is_exact_match


def test_pair_is_frozen_dataclass() -> None:
    p = Pair("t-1", "hi", "வணக்கம்", "conversation", "easy")
    with pytest.raises(Exception):  # FrozenInstanceError subclass of Exception
        p.tanglish = "changed"  # type: ignore[misc]


def test_main_cli_smoke_writes_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import eval.run as runmod

    monkeypatch.setattr(runmod, "REPORTS_DIR", tmp_path)
    rc = main(["--model", "baseline", "--sample", "3"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "baseline on v1" in captured.out
    assert "CER=" in captured.out
    reports = list(tmp_path.glob("*.md"))
    assert len(reports) == 1
    assert "Eval report" in reports[0].read_text(encoding="utf-8")


def test_main_cli_json_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    import json

    import eval.run as runmod

    monkeypatch.setattr(runmod, "REPORTS_DIR", tmp_path)
    rc = main(["--model", "baseline", "--sample", "3", "--json", "--no-report"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["model"] == "baseline"
    assert out["n"] == 3
    assert 0 <= out["cer"] <= 1.01  # allow tiny floating-point overshoot
