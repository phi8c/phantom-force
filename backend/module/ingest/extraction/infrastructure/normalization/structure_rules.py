"""Deterministic heading rules shared by every extraction provider.

Providers disagree on heading depth (Azure marks every heading level 1, Docling
levels drift per page range, Word files often carry labels only as typed text).
These rules read the label a human wrote ("Chương II", "Điều 5.", "1.2") and map
it to a stable rank, so every part of a split document agrees. Ranks are sparse;
the assembler compacts them to 1..n once the whole document is known.

The rules only repair; they never override markup that is already sound. Weak
evidence, or provider levels that already order the labels correctly, change
nothing: resolve_levels returns None and the caller keeps the provider's levels.
"""
import os
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

RULES_VERSION = "2"
APPLIED_WARNING = f"Heading levels normalized by structure rules v{RULES_VERSION}"
ENV_FLAG = "INGEST_STRUCTURE_RULES"

# Sparse ranks, outer -> inner. Decimal labels sit below every named unit.
PART, CHAPTER, SECTION, SUBSECTION, ARTICLE, EN_SECTION = 10, 20, 30, 35, 40, 45
DECIMAL_BASE = 50

_ROMAN = r"(?-i:[IVXLCDM]+)"
_LABEL = re.compile(
    r"\s*(?:"
    rf"(?P<part>(?:phần\s+(?:thứ\s+)?|part\s+)(?:\d+|{_ROMAN}|nhất|hai|ba|tư|năm|sáu|bảy|tám|chín|mười)\b)"
    rf"|(?P<chapter>(?:chương|chapter)\s+(?:\d+|{_ROMAN})\b)"
    r"|(?P<subsection>tiểu\s+mục\s+\d+\b)"
    rf"|(?P<section>mục\s+(?:\d+|{_ROMAN})\b)"
    rf"|(?P<article>(?:điều|article)\s+(?:\d+[a-zđ]?|{_ROMAN})\b)"
    r"|(?P<en_section>section\s+\d+(?:\.\d+)*\b)"
    r"|(?P<appendix>(?:phụ\s+lục|appendix|annex)\b(?:\s+(?:\d+|(?-i:[IVXLCDM]+|[A-Z]))\b)?)"
    r")", re.I)
_RANK = {"part": PART, "chapter": CHAPTER, "section": SECTION, "subsection": SUBSECTION,
         "article": ARTICLE, "en_section": EN_SECTION, "appendix": CHAPTER}
_DECIMAL = re.compile(r"\s*(?P<num>\d{1,2}(?:\.\d{1,2}){0,3})(?P<sep>[.)]?)\s+(?=\S)")
_ROMAN_LABEL = re.compile(rf"\s*(?P<num>{_ROMAN})[.)]\s+(?=\S)")
_ROMAN_VALUE = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
_WORD_VALUE = {"nhất": 1, "hai": 2, "ba": 3, "tư": 4, "năm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9, "mười": 10}
_DIGITS = re.compile(r"\d+")
_LEADER = re.compile(r"\.{4,}|…{2,}|\t\d+\s*$")
_LOOSE = frozenset({"roman", "decimal"})          # numbering that may skip a missed heading
_RESET_ON_OUTER = frozenset({"section", "subsection", "en_section", "decimal"})
_LABEL_ONLY_RANKS = frozenset({PART, CHAPTER, SECTION, SUBSECTION})
_TRUSTED_HEADINGS = 5  # provider headings (over 2+ levels) that make its markup worth trusting


@dataclass(frozen=True, slots=True)
class Resolution:
    levels: list[int | None]
    titles: dict[int, str]  # item index -> section title extended with its title line


@dataclass(frozen=True, slots=True)
class _Hit:
    rank: int
    family: str          # sequence scope: label kind, "roman" or "decimal"
    scope: tuple         # decimal parent prefix
    number: int | None
    label_only: bool     # label without its own title; the title is the next paragraph
    separated: bool = True  # "Điều 5." / "Điều 5:" rather than a bare "Điều 5 Luật này ..."


def rules_enabled() -> bool:
    return os.environ.get(ENV_FLAG) == "1"


def _ordinal(token: str) -> int | None:
    digits = _DIGITS.match(token)
    if digits:
        return int(digits.group())
    if token.isupper() and all(char in _ROMAN_VALUE for char in token):
        total = previous = 0
        for char in reversed(token):
            value = _ROMAN_VALUE[char]
            total, previous = (total - value, previous) if value < previous else (total + value, value)
        return total
    return _WORD_VALUE.get(token.lower())


def _upper_ratio(text: str) -> float:
    letters = [char for char in text[:200] if char.isalpha()]
    return sum(char.isupper() for char in letters) / len(letters) if letters else 0.0


def _is_title_line(text: str, flagged: bool) -> bool:
    text = text.strip()
    return 0 < len(text) <= 150 and text[-1] not in ".;:," and (flagged or _upper_ratio(text) >= 0.5)


def _key(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).lower().split())


def _named_hit(text: str) -> _Hit | None:
    match = _LABEL.match(text, 0, 220)
    if match is None:
        return None
    family = match.lastgroup
    rest = text[match.end():].lstrip(" \t")
    separated = rest[:1] in {".", ":", "-", "–", "—"}
    rest = rest.lstrip(".:-–—) \t")
    # "Điều 5 của Luật này" / "Điều 5, 6 và 7" are references; "Điều 5. Phạm vi" is a heading.
    if rest[:1] in {",", ";"} or (rest[:1].islower() and not separated):
        return None
    number = None if family == "appendix" else _ordinal(match.group().split()[-1])
    return _Hit(_RANK[family], family, (), number, not rest, separated)


def _numbered_hit(text: str) -> _Hit | None:
    match = _DECIMAL.match(text)
    if match is not None:
        parts = match.group("num").split(".")
        # "1." needs its dot; "1)" and "1 kW" are list items or quantities.
        if (len(parts) == 1 and match.group("sep") != ".") or not text[match.end():][:1].isupper():
            return None
        return _Hit(DECIMAL_BASE + 5 * len(parts), "decimal", tuple(parts[:-1]), int(parts[-1]), False)
    match = _ROMAN_LABEL.match(text)
    if match is None or not text[match.end():][:1].isupper():
        return None
    return _Hit(CHAPTER, "roman", (), _ordinal(match.group("num")), False)


def _form_ok(hit: _Hit, text: str) -> bool:
    size, last = len(text), text[-1]
    if _LEADER.search(text):  # table-of-contents line
        return False
    if hit.family in _LOOSE:
        return size <= 120 and last not in ";,:" and not (last == "." and size > 60)
    return size <= 250 and last not in ";," and not (last == "." and size > 120)


def _classify(text: str) -> _Hit | None:
    text = unicodedata.normalize("NFC", text.strip())  # decomposed Vietnamese would miss every label
    if not text:
        return None
    hit = _named_hit(text) or _numbered_hit(text)
    return hit if hit is not None and _form_ok(hit, text) else None


def _continues(previous: int | None, hit: _Hit) -> bool:
    number = hit.number
    if previous is None or number is None:
        return True
    if number == 1:  # a restart ("Điều 1" after Phụ lục) must look like a heading, not a citation
        return hit.separated
    if hit.family in _LOOSE:
        return previous < number <= previous + 3
    return number > previous or (number == previous and hit.family == "article")


def _contents_hits(texts: Sequence[str], hits: dict[int, _Hit]) -> set[int]:
    """Hits on consecutive lines whose title comes back later: a typed table of contents."""
    last_seen = {_key(texts[index]): index for index in sorted(hits)}
    return {index for index in hits
            if (index - 1 in hits or index + 1 in hits) and last_seen[_key(texts[index])] > index}


def _with_children(hits: dict[int, _Hit]) -> set[int]:
    """Top-level numbered hits that really own sub-numbered hits, as a heading does and a list item does not."""
    owners, roman, top = set(), None, None
    for index in sorted(hits):
        hit = hits[index]
        if hit.family == "roman":
            roman, top = index, None
        elif hit.family == "decimal" and not hit.scope:
            if roman is not None:
                owners.add(roman)
            top = (index, str(hit.number))
        elif hit.family == "decimal" and top is not None and hit.scope == (top[1],):
            owners.add(top[0])
    return owners


def _accept(hits: dict[int, _Hit], levels: Sequence[int | None], texts: Sequence[str],
            trusted: bool) -> dict[int, _Hit]:
    """Keep hits that continue their own numbering and are not body list items."""
    owners = _with_children(hits)
    last: dict[tuple, int] = {}
    accepted: dict[int, _Hit] = {}
    in_article = False
    for index in sorted(hits):
        hit = hits[index]
        if hit.family in _LOOSE:
            if in_article or (trusted and levels[index] is None):
                continue  # khoản/điểm inside an Điều, or numbering the trusted provider chose not to mark
            title = texts[index]
            strong = levels[index] is not None or _upper_ratio(title) >= 0.6
            strong = strong or (len(title) <= 100 if hit.scope else index in owners)
            if not strong:
                continue
        key = (hit.family, hit.scope)
        if not _continues(last.get(key), hit):
            continue
        if hit.number is not None:
            last[key] = hit.number
        accepted[index] = hit
        if hit.rank <= CHAPTER:
            for stale in [k for k in last if k[0] in _RESET_ON_OUTER]:
                del last[stale]
        if hit.rank <= SUBSECTION:
            in_article = False
        elif hit.rank == ARTICLE:
            in_article = True
    return accepted


def _already_consistent(accepted: dict[int, _Hit], levels: Sequence[int | None]) -> bool:
    """Provider levels that already put every labeled rank below the one above it need no help."""
    spans: dict[int, tuple[int, int]] = {}
    for index, hit in accepted.items():
        if levels[index] is None:
            return False
        low, high = spans.get(hit.rank, (levels[index], levels[index]))
        spans[hit.rank] = (min(low, levels[index]), max(high, levels[index]))
    ordered = [spans[rank] for rank in sorted(spans)]
    return len(ordered) >= 2 and all(left[1] < right[0] for left, right in zip(ordered, ordered[1:]))


def resolve_levels(texts: Sequence[str], levels: Sequence[int | None]) -> Resolution | None:
    """Return stable heading levels for text items, or None to keep the provider's."""
    hits = {}
    for index, text in enumerate(texts):
        hit = _classify(text)
        if hit is not None:
            hits[index] = hit
    for index in _contents_hits(texts, hits):
        del hits[index]
    if not hits:
        return None
    marked = [level for level in levels if level is not None]
    trusted = len(marked) >= _TRUSTED_HEADINGS and len(set(marked)) >= 2
    accepted = _accept(hits, levels, texts, trusted)
    named = sum(h.family not in _LOOSE for h in accepted.values())
    if named < 2 and len(accepted) < 3:
        return None
    if _already_consistent(accepted, levels):
        return None
    resolved: list[int | None] = [None] * len(texts)
    titles: dict[int, str] = {}
    owner = None
    for index, text in enumerate(texts):
        hit = accepted.get(index)
        if hit is not None:
            resolved[index] = hit.rank
            owner = index if hit.label_only and hit.rank in _LABEL_ONLY_RANKS else None
            continue
        if owner is not None:
            pending, owner = owner, None
            if _is_title_line(text, levels[index] is not None):
                titles[pending] = text.strip()
    # A provider heading without a label stays plain text: placing it would add a level that
    # pushes every Điều down and breaks the chunk level the pipeline is configured for.
    return Resolution(resolved, titles)
