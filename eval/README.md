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

## Running the real IndicXlit model

The `indicxlit` model is registered but requires the optional `ai4bharat-transliteration`
package. Two ways to use it:

**Locally on Linux or Python 3.11 (Windows Python 3.13 is broken — fairseq build fails):**

```bash
uv add --package tamil-edu-transliterate "ai4bharat-transliteration>=1.1.3"
uv run python -m eval.run --model indicxlit --set v1
```

First call downloads ~1GB model, cached after that.

**In CI (recommended):** the `.github/workflows/eval-real.yml` workflow runs this
automatically on a weekly schedule (Sundays 03:00 UTC), on any push to `main` that
touches eval/data/transliterate code, and on manual trigger. Reports are committed
back to `eval/reports/`. The S1-1 acceptance gate (CER ≤ 0.15) is enforced — workflow
fails if quality regresses below threshold.

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
