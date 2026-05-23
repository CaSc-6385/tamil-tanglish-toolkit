"""Tests for the public top-level `transliterate()` convenience function."""

from __future__ import annotations

import pytest
from tamil_edu_transliterate import (
    BaselineTransliterator,
    TransliterationError,
    Transliterator,
    transliterate,
)


def test_default_backend_is_baseline() -> None:
    assert transliterate("vanakkam") == "vanakkam"


def test_explicit_baseline_backend_works() -> None:
    assert transliterate("nanba", backend="baseline") == "nanba"


def test_unknown_backend_raises_valueerror() -> None:
    with pytest.raises(ValueError, match="Unknown backend"):
        transliterate("hi", backend="does-not-exist")


def test_topk_passes_through() -> None:
    # Baseline ignores topk but mustn't crash on any value
    assert transliterate("hi", topk=10) == "hi"


def test_backends_are_cached_across_calls() -> None:
    """Same backend instance should be reused — proves the singleton dict works."""
    from tamil_edu_transliterate import _BACKENDS

    _BACKENDS.clear()
    transliterate("a")
    transliterate("b")
    assert len(_BACKENDS) == 1
    assert "baseline" in _BACKENDS


def test_exports_are_public() -> None:
    """Smoke test that the symbols we promise in __all__ actually import."""
    import tamil_edu_transliterate as tx

    for name in [
        "transliterate",
        "BaselineTransliterator",
        "IndicXlitTransliterator",
        "Transliterator",
        "TransliterationError",
    ]:
        assert hasattr(tx, name), f"missing public export: {name}"


def test_transliterator_protocol_runtime_checkable() -> None:
    """A custom class implementing the right shape should satisfy isinstance check."""

    class Stub:
        name = "stub"

        def transliterate(self, text: str, *, topk: int = 1) -> str:
            return text

        def alternatives(self, text: str, *, topk: int = 3) -> list[str]:
            return [text]

    assert isinstance(Stub(), Transliterator)
    assert isinstance(BaselineTransliterator(), Transliterator)


def test_transliteration_error_is_runtimeerror() -> None:
    """Confirm the error class is a RuntimeError subclass — useful for catch blocks."""
    assert issubclass(TransliterationError, RuntimeError)
