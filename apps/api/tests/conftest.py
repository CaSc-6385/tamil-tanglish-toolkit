"""Pytest configuration for the API tests.

Pin TRANSLITERATE_BACKEND=baseline so existing contract tests (which assert
passthrough output) stay deterministic regardless of production default.
Individual tests that want a different backend can use monkeypatch.setenv.

Module-level setdefault — runs when pytest imports conftest, before any test
module is imported. (pytest_configure hook is the alternative but it
PluginValidationError's on stricter pluggy versions if the signature is wrong.)
"""

from __future__ import annotations

import os

os.environ.setdefault("TRANSLITERATE_BACKEND", "baseline")
# Pin OCR to the no-op baseline so /ocr contract tests are deterministic and do
# not require the system Tesseract binary. Tests that need real/extracted text
# monkeypatch the OCR engine directly.
os.environ.setdefault("OCR_BACKEND", "baseline")
