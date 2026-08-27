"""Japanese text processing for lyrics rendering.

Handles Japanese text normalization, segmentation, and romaji conversion.
Not yet implemented - design document only.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal


# Japanese character ranges
HIRAGANA_RANGE = (0x3040, 0x309F)
KATAKANA_RANGE = (0x30A0, 0x30FF)
KANJI_RANGE = (0x4E00, 0x9FFF)
KANJI_EXT_A = (0x3400, 0x4DBF)


def is_japanese(ch: str) -> bool:
    """Check if character is Japanese (hiragana, katakana, or kanji)."""
    if not ch:
        return False
    code = ord(ch)
    return (
        HIRAGANA_RANGE[0] <= code <= HIRAGANA_RANGE[1] or
        KATAKANA_RANGE[0] <= code <= KATAKANA_RANGE[1] or
        KANJI_RANGE[0] <= code <= KANJI_RANGE[1] or
        KANJI_EXT_A[0] <= code <= KANJI_EXT_A[1]
    )


def is_hiragana(ch: str) -> bool:
    """Check if character is hiragana."""
    if not ch:
        return False
    code = ord(ch)
    return HIRAGANA_RANGE[0] <= code <= HIRAGANA_RANGE[1]


def is_katakana(ch: str) -> bool:
    """Check if character is katakana."""
    if not ch:
        return False
    code = ord(ch)
    return KATAKANA_RANGE[0] <= code <= KATAKANA_RANGE[1]


def is_kanji(ch: str) -> bool:
    """Check if character is kanji."""
    if not ch:
        return False
    code = ord(ch)
    return (
        KANJI_RANGE[0] <= code <= KANJI_RANGE[1] or
        KANJI_EXT_A[0] <= code <= KANJI_EXT_A[1]
    )


def normalize_japanese(text: str) -> str:
    """Normalize Japanese text for consistent rendering.
    
    - NFKC normalization
    - Convert full-width to half-width for ASCII
    - Normalize prolonged sound marks
    """
    # Normalize prolonged sound marks BEFORE NFKC (NFKC converts ～ to ~)
    text = text.replace("～", "ー")  # Wave dash to chōon
    
    # NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    
    # Convert full-width ASCII to half-width
    text = text.translate(str.maketrans(
        "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    ))
    
    return text


def has_japanese(text: str) -> bool:
    """Check if text contains any Japanese characters."""
    return any(is_japanese(ch) for ch in text)


def count_japanese_chars(text: str) -> dict[str, int]:
    """Count Japanese characters by type."""
    counts = {"hiragana": 0, "katakana": 0, "kanji": 0, "other": 0}
    for ch in text:
        if is_hiragana(ch):
            counts["hiragana"] += 1
        elif is_katakana(ch):
            counts["katakana"] += 1
        elif is_kanji(ch):
            counts["kanji"] += 1
        else:
            counts["other"] += 1
    return counts


class JapaneseMode:
    """Japanese rendering mode."""
    ROMAJI = "romaji"
    HIRAGANA = "hiragana"
    KATAKANA = "katakana"
    MIXED = "mixed"
    AUTO = "auto"


def convert_japanese_mode(
    text: str,
    mode: Literal["romaji", "hiragana", "katakana", "mixed", "auto"] = "auto",
    kanji_fallback: Literal["hiragana", "romaji"] = "hiragana"
) -> str:
    """Convert Japanese text based on rendering mode.
    
    Args:
        text: Input Japanese text
        mode: Rendering mode
        kanji_fallback: How to handle kanji in mixed mode
        
    Returns:
        Converted text for rendering
    """
    if mode == "romaji":
        return to_romaji(text)
    
    if mode == "hiragana":
        return to_hiragana(text)
    
    if mode == "katakana":
        return to_katakana(text)
    
    if mode == "mixed":
        return convert_mixed(text, kanji_fallback)
    
    if mode == "auto":
        # Auto-detect: if mostly Japanese, use mixed
        counts = count_japanese_chars(text)
        if counts["hiragana"] + counts["katakana"] + counts["kanji"] > len(text) * 0.5:
            return convert_mixed(text, kanji_fallback)
        return text
    
    return text


def to_romaji(text: str) -> str:
    """Convert Japanese text to romaji."""
    # TODO: Implement with pykakasi
    # import pykakasi
    # kks = pykakasi.kakasi()
    # result = kks.convert(text)
    # return " ".join([r["hepburn"] for r in result])
    return text  # Placeholder


def to_hiragana(text: str) -> str:
    """Convert katakana to hiragana."""
    # Convert katakana to hiragana
    result = []
    for ch in text:
        code = ord(ch)
        if KATAKANA_RANGE[0] <= code <= KATAKANA_RANGE[1]:
            # Katakana to hiragana: subtract 0x60
            result.append(chr(code - 0x60))
        else:
            result.append(ch)
    return "".join(result)


def to_katakana(text: str) -> str:
    """Convert hiragana to katakana."""
    result = []
    for ch in text:
        code = ord(ch)
        if HIRAGANA_RANGE[0] <= code <= HIRAGANA_RANGE[1]:
            # Hiragana to katakana: add 0x60
            result.append(chr(code + 0x60))
        else:
            result.append(ch)
    return "".join(result)


def convert_mixed(text: str, kanji_fallback: str = "hiragana") -> str:
    """Convert text for mixed rendering.
    
    - Hiragana: keep as-is
    - Katakana: keep as-is (or convert to hiragana)
    - Kanji: convert to hiragana/romaji based on fallback
    - Latin: keep as-is
    """
    result = []
    for ch in text:
        if is_hiragana(ch):
            result.append(ch)
        elif is_katakana(ch):
            result.append(ch)  # Keep katakana
        elif is_kanji(ch):
            if kanji_fallback == "hiragana":
                # Convert kanji to hiragana reading
                # TODO: Use fugashi/MeCab for reading
                result.append(ch)  # Placeholder
            else:
                # Convert to romaji
                # TODO: Use pykakasi
                result.append(ch)  # Placeholder
        else:
            result.append(ch)
    return "".join(result)