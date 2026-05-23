"""Pytest fixtures for the API tests.

Pin TRANSLITERATE_BACKEND=baseline by default so existing contract tests
(which assert passthrough output) stay deterministic. Individual tests that
want a different backend can monkeypatch the env var.
"""

from __future__ import annotations

import os


def pytest_configure(_config: object) -> None:
    os.environ.setdefault("TRANSLITERATE_BACKEND", "baseline")
