# tamil-edu-ocr

Printed Tamil / Tanglish **image → text** OCR. Pluggable backends behind a single `OcrEngine` protocol — mirrors the design of `tamil-edu-transliterate`.

## Backends

| Backend   | Class                | Deps                          | Notes                                                                      |
| --------- | -------------------- | ----------------------------- | -------------------------------------------------------------------------- |
| Baseline  | `BaselineOcrEngine`  | none                          | No-op. Returns empty text — eval lower bound + a stand-in for tests/CI     |
| Tesseract | `TesseractOcrEngine` | `pytesseract`, `pillow` + bin | Tesseract 5 LSTM, lang `tam+eng`. CPU-only, fits the Fly.io/Hetzner budget |

PLAN.md S3 also lists TrOCR + PaddleOCR backends; they slot in behind the same
`OcrEngine` protocol when the GPU/accuracy budget allows.

## Install

```bash
# core only (baseline)
uv add tamil-edu-ocr

# with the Tesseract backend
uv add 'tamil-edu-ocr[tesseract]'
```

The Tesseract backend needs the system binary + Tamil language data:

```bash
brew install tesseract tesseract-lang                  # macOS
apt-get install tesseract-ocr tesseract-ocr-tam        # Debian/Ubuntu
```

## Usage

```python
from tamil_edu_ocr import ocr

with open("note.png", "rb") as f:
    result = ocr(f.read(), backend="tesseract")

result.text            # "naan tamil padikiren"
result.avg_confidence  # 0.92
result.lines           # [OcrLine(text="naan tamil padikiren", confidence=0.92)]
```

`OcrError` is raised for unreadable images or engine failures; `ValueError` for an
unknown backend name.

## In the API

`apps/api` exposes this as `POST /ocr` (multipart upload → text + per-line
confidence, 10 MB cap). Pick the backend at runtime with the `OCR_BACKEND` env var
(`tesseract` default, `baseline` for tests). The extracted text feeds straight into
`POST /translate` for the image → transliterate → correct chain.
