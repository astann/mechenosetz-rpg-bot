"""Проверка имени героя на нежелательные слова."""

from __future__ import annotations

import re

_BAD_WORDS: tuple[str, ...] = (
    "хуй",
    "пизда",
    "еблан",
    "блядь",
    "блять",
    "сука",
    "нахуй",
    "nigger",
    "nigga",
    "faggot",
    "fuck",
    "cunt",
    "bitch",
    "whore",
)

_BAD_STEMS: tuple[str, ...] = (
    "бляд",
    "пизд",
    "хуй",
    "ебл",
    "еба",
    "сук",
    "долбо",
    "fagg",
    "nigg",
)


def _normalize(s: str) -> str:
    s = s.lower().replace("ё", "е")
    s = re.sub(r"[^a-zа-я0-9]+", "", s)
    return s


def _tokens(s: str) -> list[str]:
    s = s.lower().replace("ё", "е")
    return [t for t in re.split(r"[^a-zа-я0-9]+", s) if t]


def has_bad_words(name: str) -> bool:
    tokens = _tokens(name)
    if not tokens:
        return False
    bad_words = set(_BAD_WORDS)
    for token in tokens:
        n = _normalize(token)
        if not n:
            continue
        if n in bad_words:
            return True
        if any(stem in n for stem in _BAD_STEMS):
            return True
    return False
