"""Token classifier for code-switched Tanglish input.

The job: when a user types `send the message ku reply pannu`, we want
`send`, `the`, `message`, `reply` to pass through verbatim (they're English)
while `ku`, `pannu` get transliterated as Tanglish.

Rules (in order):
1. Whitespace → kind=WHITESPACE
2. All-punctuation → kind=PUNCTUATION
3. ALL-CAPS length >= 2 → kind=ENGLISH (acronyms like USA, NASA)
4. Mixed-case with internal capitals → kind=ENGLISH (brand names like WhatsApp, YouTube)
5. Exact match in the common-English dictionary → kind=ENGLISH
6. Otherwise → kind=TANGLISH (transliterate me)

The dictionary is intentionally small (~250 words) and biased toward what
Tamil-learning kids actually type: greetings (`hi`, `bye`), school terms
(`homework`, `exam`, `class`), tech (`message`, `link`, `share`, `like`),
and common articles/prepositions (`the`, `to`, `from`, `with`).

Expanding the dictionary is cheap — add words below + add a test in
`tests/test_tokenizer.py`. Misclassifications are easy to spot in eval reports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class TokenKind(StrEnum):
    TANGLISH = "tanglish"  # transliterate me
    ENGLISH = "english"  # pass through verbatim
    PUNCTUATION = "punctuation"  # pass through, but separate token
    WHITESPACE = "whitespace"  # pass through


@dataclass(frozen=True)
class Token:
    text: str
    kind: TokenKind


# Common English words a Tamil-learning kid is likely to code-switch with.
# Lowercased for matching. Keep this list small + curated — expansion based on
# misclassification feedback from eval reports.
_ENGLISH_WORDS = frozenset(
    [
        # articles / determiners / pronouns
        "a",
        "an",
        "the",
        "this",
        "that",
        "these",
        "those",
        "my",
        "your",
        "his",
        "her",
        "its",
        "our",
        "their",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "us",
        "them",
        # common prepositions
        "of",
        "to",
        "from",
        "in",
        "on",
        "at",
        "by",
        "for",
        "with",
        "about",
        "into",
        "onto",
        "over",
        "under",
        "between",
        "through",
        # common conjunctions
        "and",
        "or",
        "but",
        "so",
        "if",
        "then",
        "than",
        "because",
        # school
        "homework",
        "exam",
        "test",
        "class",
        "school",
        "teacher",
        "student",
        "book",
        "pencil",
        "pen",
        "paper",
        "notebook",
        "lesson",
        "grade",
        "math",
        "maths",
        "science",
        "english",
        "tamil",
        "history",
        "study",
        # tech / messaging
        "message",
        "msg",
        "text",
        "call",
        "phone",
        "video",
        "audio",
        "photo",
        "picture",
        "link",
        "share",
        "like",
        "post",
        "comment",
        "follow",
        "reply",
        "send",
        "delete",
        "search",
        "google",
        "youtube",
        "whatsapp",
        "instagram",
        "facebook",
        "tiktok",
        "snapchat",
        "twitter",
        "email",
        "internet",
        "wifi",
        "online",
        "offline",
        "download",
        "upload",
        "click",
        "tap",
        "swipe",
        "scroll",
        # everyday
        "yes",
        "no",
        "ok",
        "okay",
        "hi",
        "hello",
        "bye",
        "thanks",
        "please",
        "sorry",
        "morning",
        "evening",
        "night",
        "today",
        "tomorrow",
        "yesterday",
        "now",
        "later",
        "soon",
        "always",
        "never",
        # actions / verbs (already common in Tanglish)
        "do",
        "did",
        "done",
        "make",
        "made",
        "go",
        "going",
        "went",
        "come",
        "came",
        "see",
        "saw",
        "want",
        "need",
        "have",
        "has",
        "had",
        "get",
        "got",
        "give",
        "took",
        "take",
        "find",
        "found",
        "buy",
        "bought",
        "sell",
        "sold",
        "open",
        "close",
        "start",
        "stop",
        "wait",
        "watch",
        "use",
        "play",
        "work",
        "read",
        "write",
        "show",
        "tell",
        "ask",
        "answer",
        "help",
        "try",
        "fix",
        "check",
        "save",
        # devices / objects
        "laptop",
        "phone",
        "mobile",
        "tablet",
        "computer",
        "tv",
        "screen",
        "camera",
        "charger",
        "cable",
        "headphones",
        "speaker",
        "battery",
        "bag",
        "key",
        "door",
        "car",
        "bike",
        "bus",
        "train",
        # places (loanwords kids type in English)
        "office",
        "park",
        "shop",
        "store",
        "market",
        "mall",
        "hospital",
        "hotel",
        "restaurant",
        "cafe",
        "airport",
        "station",
        "house",
        "room",
        # numbers as words (rare in Tanglish; usually digit input)
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "first",
        "second",
        "third",
        "last",
        # misc
        "good",
        "bad",
        "nice",
        "great",
        "fine",
        "happy",
        "sad",
        "fun",
        "easy",
        "hard",
        "fast",
        "slow",
        "new",
        "old",
        "big",
        "small",
        "all",
        "some",
        "any",
        "many",
        "few",
        "more",
        "less",
        "only",
        "very",
    ]
)


# Regex: keeps whitespace, single-punctuation tokens, and word chunks.
# Same as the one in indicxlit.py; duplicated here so this module is standalone.
_TOKEN_RE = re.compile(r"\s+|[^\w\s]|[\w]+", flags=re.UNICODE)

# Letters only (ASCII or Unicode), at least one char
_ALPHA_RE = re.compile(r"^[A-Za-z-￿]+$")


def _classify_word(word: str) -> TokenKind:
    """Classify a single word token (no whitespace, no punctuation)."""
    lower = word.lower()

    # All-caps acronym: USA, NASA, AI, ML
    if len(word) >= 2 and word.isupper() and word.isascii():
        return TokenKind.ENGLISH

    # Brand name with internal capitals: WhatsApp, YouTube, iPhone
    if len(word) >= 2 and word[1:] != word[1:].lower() and word.isascii():
        return TokenKind.ENGLISH

    # Dictionary match
    if lower in _ENGLISH_WORDS:
        return TokenKind.ENGLISH

    # Default: Tanglish (transliterate)
    return TokenKind.TANGLISH


def tokenize(text: str) -> list[Token]:
    """Split text into typed tokens preserving original order and spacing.

    Reassembly via `"".join(t.text for t in tokenize(text))` is lossless.
    """
    if not text:
        return []
    out: list[Token] = []
    for chunk in _TOKEN_RE.findall(text):
        if chunk.isspace():
            out.append(Token(chunk, TokenKind.WHITESPACE))
        elif _ALPHA_RE.match(chunk):
            out.append(Token(chunk, _classify_word(chunk)))
        else:
            # Mixed (e.g. "co-op", "U.S.A.") or pure punctuation/digit
            # Conservative: treat as PUNCTUATION (passthrough)
            out.append(Token(chunk, TokenKind.PUNCTUATION))
    return out
