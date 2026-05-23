# eval — Tanglish→Tamil eval harness

Runs the **golden eval set** (`data/golden/v1.csv` once S0-4 ships; built-in 10-pair sample until then) against any registered model and emits a markdown report with CER, WER, BLEU, chrF, exact-match rate, per-domain breakdown, and the worst-10 errors.

## Quick start

```bash
# from repo root
uv run python -m eval.run --model baseline --sample 10
uv run python -m eval.run --model baseline --set v1 --domain conversation
uv run python -m eval.run --model baseline --json --no-report  # CI-friendly
```

Reports land in `eval/reports/YYYY-MM-DD-HHMMSS-<model>-<set>.md`.

## Registering a new model

In `eval/run.py`, implement the `Model` protocol and add to `MODELS`:

```python
class MyModel:
    name = "my-model"
    def predict(self, tanglish: str) -> str:
        return my_translate(tanglish)

MODELS["my-model"] = MyModel
```

Then: `uv run python -m eval.run --model my-model`.

## Running real-model eval

Three models are registered: `baseline` (passthrough), `aksharamukha` (rule-based,
real Tamil), `indicxlit` (ML — currently blocked, see ADR-0002).

### aksharamukha (works today)

```bash
uv run python -m eval.run --model aksharamukha --set v1
```

Pure Python, no ML deps, works on any Python version. **Quality is rough**: CER
~35% on golden v1 (rule-based ceiling on Tanglish). Used as the working "real
backend" until IndicXlit is unblocked. The `.github/workflows/eval-real.yml`
workflow runs this automatically.

### IndicXlit (currently blocked)

The `indicxlit` model is registered but **cannot run today** — its dep
`fairseq` has a `mutable default dataclass` error that breaks on Python ≥ 3.11,
and our project requires Python ≥ 3.11. See [ADR-0002](../docs/adr/0002-indicxlit-deferred.md)
for the full analysis and unblock criteria.

When fairseq is fixed:

```bash
uv add --package tamil-edu-transliterate "ai4bharat-transliteration>=1.1.3"
uv run python -m eval.run --model indicxlit --set v1
```

### S1-1 acceptance status

PLAN.md S1-1 target is CER ≤ 15%. **Not met** today (aksharamukha is at 35%;
IndicXlit blocked). Tracked as carry-over to a future sprint per ADR-0002.

## Golden set schema (`data/golden/v1.csv`)

| Column           | Type   | Notes                                                        |
| ---------------- | ------ | ------------------------------------------------------------ |
| `id`             | string | Stable identifier, e.g. `conv-042`                           |
| `tanglish`       | string | Input                                                        |
| `expected_tamil` | string | Tamil Unicode target                                         |
| `domain`         | enum   | `conversation` / `names` / `school` / `news` / `code_switch` |
| `difficulty`     | enum   | `easy` / `medium` / `hard`                                   |
| `reviewer`       | string | Initials of native-speaker reviewer                          |
| `notes`          | string | Free text                                                    |

See `docs/TESTING.md` §4.1 for composition rules.

## Metrics

| Metric          | Formula                                | Lower/Higher = better |
| --------------- | -------------------------------------- | --------------------- |
| **CER**         | jiwer character error rate             | lower                 |
| **WER**         | jiwer word error rate                  | lower                 |
| **BLEU-4**      | sacrebleu corpus BLEU                  | higher                |
| **chrF**        | sacrebleu character-F                  | higher                |
| **Exact match** | strict string equality after `strip()` | higher                |

Targets per sprint in `docs/TESTING.md` §4.2.
