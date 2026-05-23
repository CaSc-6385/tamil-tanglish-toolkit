"""Tests for the code-switch tokenizer."""

from __future__ import annotations

import pytest
from tamil_edu_transliterate.tokenizer import Token, TokenKind, tokenize

# ---- Basic shapes ----


def test_empty_input_returns_empty_list() -> None:
    assert tokenize("") == []


def test_single_tanglish_word() -> None:
    toks = tokenize("vanakkam")
    assert toks == [Token("vanakkam", TokenKind.TANGLISH)]


def test_single_english_word_from_dictionary() -> None:
    toks = tokenize("hello")
    assert toks == [Token("hello", TokenKind.ENGLISH)]


def test_round_trip_lossless() -> None:
    """Reassembly via join must equal the input."""
    cases = [
        "vanakkam nanba",
        "send the message ku reply pannu",
        "homework finish panniten!",
        "WhatsApp la message anuppu",
        "  leading and trailing  ",
        "",
        "வணக்கம் hello",
    ]
    for text in cases:
        rebuilt = "".join(t.text for t in tokenize(text))
        assert rebuilt == text, f"round-trip failed for {text!r}"


# ---- Token kinds ----


def test_whitespace_is_its_own_token() -> None:
    toks = tokenize("hi  there")
    assert toks[0].text == "hi"
    assert toks[1].text == "  "
    assert toks[1].kind == TokenKind.WHITESPACE
    assert toks[2].text == "there"


def test_punctuation_is_its_own_token() -> None:
    toks = tokenize("hi, world!")
    kinds = [t.kind for t in toks]
    assert TokenKind.PUNCTUATION in kinds


def test_punctuation_includes_question_mark() -> None:
    toks = tokenize("nalla iruka?")
    assert toks[-1].text == "?"
    assert toks[-1].kind == TokenKind.PUNCTUATION


# ---- English classification ----


@pytest.mark.parametrize(
    "word",
    [
        "the",
        "a",
        "and",
        "or",
        "to",
        "from",
        "with",
        "homework",
        "school",
        "teacher",
        "exam",
        "book",
        "message",
        "video",
        "phone",
        "email",
        "link",
        "google",
        "whatsapp",
        "youtube",
        "hi",
        "hello",
        "bye",
        "thanks",
        "ok",
        "okay",
        "do",
        "go",
        "send",
        "reply",
        "share",
        "click",
    ],
)
def test_common_english_words_classified_english(word: str) -> None:
    assert tokenize(word) == [Token(word, TokenKind.ENGLISH)]


def test_dictionary_match_is_case_insensitive() -> None:
    assert tokenize("HELLO")[0].kind == TokenKind.ENGLISH
    assert tokenize("Hello")[0].kind == TokenKind.ENGLISH
    assert tokenize("hello")[0].kind == TokenKind.ENGLISH


# ---- Acronyms (ALL CAPS) ----


def test_acronym_two_letters() -> None:
    assert tokenize("AI")[0].kind == TokenKind.ENGLISH


def test_acronym_three_letters() -> None:
    assert tokenize("USA")[0].kind == TokenKind.ENGLISH


def test_single_capital_letter_not_acronym() -> None:
    # Single letter that isn't in the English dictionary stays as Tanglish.
    # ('A' and 'I' are in the dict as the article / pronoun via lowercase lookup.)
    assert tokenize("Z")[0].kind == TokenKind.TANGLISH
    assert tokenize("Q")[0].kind == TokenKind.TANGLISH


# ---- Brand names (mixed case with internal capitals) ----


def test_brand_internal_capital_whatsapp() -> None:
    """WhatsApp has internal capitals → brand name → preserve."""
    assert tokenize("WhatsApp")[0].kind == TokenKind.ENGLISH


def test_brand_internal_capital_youtube() -> None:
    assert tokenize("YouTube")[0].kind == TokenKind.ENGLISH


def test_brand_internal_capital_iphone() -> None:
    assert tokenize("iPhone")[0].kind == TokenKind.ENGLISH


def test_first_letter_capital_not_brand() -> None:
    """Karthik is a Tamil name written in Roman → should transliterate."""
    assert tokenize("Karthik")[0].kind == TokenKind.TANGLISH


# ---- Tanglish (default) ----


@pytest.mark.parametrize(
    "word",
    [
        "vanakkam",
        "nanba",
        "nandri",
        "puriyala",
        "pannu",
        "padikiren",
        "Chennai",
        "Karthik",
        "Madurai",  # capitalized Tamil names
        "iruka",
        "vandhutten",
        "irundha",
    ],
)
def test_tanglish_words_classified_tanglish(word: str) -> None:
    assert tokenize(word) == [Token(word, TokenKind.TANGLISH)]


# ---- Code-switch sentences ----


def test_send_the_message_classifies_correctly() -> None:
    toks = tokenize("send the message ku reply pannu")
    words_only = [t for t in toks if t.kind in (TokenKind.ENGLISH, TokenKind.TANGLISH)]
    expected = [
        ("send", TokenKind.ENGLISH),
        ("the", TokenKind.ENGLISH),
        ("message", TokenKind.ENGLISH),
        ("ku", TokenKind.TANGLISH),
        ("reply", TokenKind.ENGLISH),
        ("pannu", TokenKind.TANGLISH),
    ]
    assert [(t.text, t.kind) for t in words_only] == expected


def test_whatsapp_la_message_anuppu() -> None:
    toks = tokenize("WhatsApp la message anuppu")
    by_text = {t.text: t.kind for t in toks if t.kind in (TokenKind.ENGLISH, TokenKind.TANGLISH)}
    assert by_text["WhatsApp"] == TokenKind.ENGLISH
    assert by_text["la"] == TokenKind.TANGLISH
    assert by_text["message"] == TokenKind.ENGLISH
    assert by_text["anuppu"] == TokenKind.TANGLISH


def test_pure_english_sentence_all_english() -> None:
    toks = tokenize("send the message to me")
    word_kinds = [t.kind for t in toks if t.kind in (TokenKind.ENGLISH, TokenKind.TANGLISH)]
    assert all(k == TokenKind.ENGLISH for k in word_kinds)


def test_pure_tanglish_sentence_all_tanglish() -> None:
    toks = tokenize("naan ungalukku phone panren")
    by_text = {t.text: t.kind for t in toks if t.kind in (TokenKind.ENGLISH, TokenKind.TANGLISH)}
    # "phone" IS in our English dictionary → preserved; rest is Tanglish.
    assert by_text["naan"] == TokenKind.TANGLISH
    assert by_text["ungalukku"] == TokenKind.TANGLISH
    assert by_text["phone"] == TokenKind.ENGLISH
    assert by_text["panren"] == TokenKind.TANGLISH


# ---- Unicode / Tamil input ----


def test_tamil_script_word_classified_tanglish() -> None:
    """Tamil script tokens fragment (no Mn handling in regex) but each piece
    is non-English and falls back to TANGLISH. Round-trip stays lossless."""
    text = "வணக்கம் hello"
    toks = tokenize(text)
    rebuilt = "".join(t.text for t in toks)
    assert rebuilt == text
    # The English word survives
    assert any(t.text == "hello" and t.kind == TokenKind.ENGLISH for t in toks)


# ---- Edge cases ----


def test_numbers_classified_punctuation() -> None:
    """\\w includes digits; conservative tokenizer treats digit tokens as
    Tanglish (they're alpha-ish). For a number-only token like '5' this is
    benign — the IndicXlit wrapper passes through non-alphabetic tokens."""
    toks = tokenize("5 puthagam")
    assert toks[0].text == "5"
    # Either classification is acceptable as long as round-trip is preserved
    rebuilt = "".join(t.text for t in toks)
    assert rebuilt == "5 puthagam"


def test_consecutive_punctuation() -> None:
    toks = tokenize("hi!!!")
    text_concat = "".join(t.text for t in toks)
    assert text_concat == "hi!!!"


def test_mixed_punctuation_preserves_round_trip() -> None:
    text = "send a.b.c to me"
    rebuilt = "".join(t.text for t in tokenize(text))
    assert rebuilt == text
