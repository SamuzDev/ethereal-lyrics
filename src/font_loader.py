"""Unified font loader for multi-script lyrics rendering.

Combines Latin, Hiragana, Katakana, and Kanji fonts.
Not yet implemented - design document only.
"""

from __future__ import annotations

# from src.font import FONT as LATIN_FONT
# from src.font_hiragana import HIRAGANA_FONT
# from src.font_katakana import KATAKANA_FONT
# from src.font_kanji import KANJI_FONT  # Optional, large


def get_combined_font() -> dict[str, list[str]]:
    """Get combined font dictionary for all supported scripts.
    
    Returns:
        Dict mapping character -> 7-row glyph (6 chars wide each row)
    """
    font = {}
    
    # Latin (existing)
    # font.update(LATIN_FONT)
    
    # Hiragana
    # font.update(HIRAGANA_FONT)
    
    # Katakana
    # font.update(KATAKANA_FONT)
    
    # Kanji (common only, optional)
    # font.update(KANJI_FONT)
    
    return font


def get_font_for_char(ch: str) -> list[str] | None:
    """Get glyph for a specific character.
    
    Args:
        ch: Single character to look up
        
    Returns:
        7-row glyph or None if not found
    """
    font = get_combined_font()
    return font.get(ch)


def get_script_for_char(ch: str) -> str:
    """Detect script for a character.
    
    Args:
        ch: Single character
        
    Returns:
        Script name: 'latin', 'hiragana', 'katakana', 'kanji', 'unknown'
    """
    if not ch:
        return 'unknown'
    
    code = ord(ch)
    
    # Latin (ASCII + extended)
    if code <= 0x024F:  # Latin Extended-B
        return 'latin'
    
    # Hiragana: U+3040-U+309F
    if 0x3040 <= code <= 0x309F:
        return 'hiragana'
    
    # Katakana: U+30A0-U+30FF
    if 0x30A0 <= code <= 0x30FF:
        return 'katakana'
    
    # Kanji (CJK Unified Ideographs): U+4E00-U+9FFF
    # Also includes extensions
    if 0x4E00 <= code <= 0x9FFF:
        return 'kanji'
    if 0x3400 <= code <= 0x4DBF:  # CJK Extension A
        return 'kanji'
    if 0x20000 <= code <= 0x2A6DF:  # CJK Extension B
        return 'kanji'
    
    return 'unknown'


def split_mixed_text(text: str) -> list[tuple[str, str]]:
    """Split mixed-script text into (script, substring) segments.
    
    Args:
        text: Input text with mixed scripts
        
    Returns:
        List of (script, substring) tuples
    """
    if not text:
        return []
    
    segments = []
    current_script = get_script_for_char(text[0])
    current_segment = text[0]
    
    for ch in text[1:]:
        script = get_script_for_char(ch)
        if script == current_script:
            current_segment += ch
        else:
            segments.append((current_script, current_segment))
            current_script = script
            current_segment = ch
    
    segments.append((current_script, current_segment))
    return segments


def convert_to_romaji(text: str) -> str:
    """Convert Japanese text to romaji (fallback).
    
    Args:
        text: Japanese text (hiragana/katakana/kanji)
        
    Returns:
        Romaji representation
    """
    # TODO: Implement with pykakasi
    # import pykakasi
    # kks = pykakasi.kakasi()
    # result = kks.convert(text)
    # return " ".join([r["hepburn"] for r in result])
    return text  # Placeholder


def segment_japanese(text: str) -> list[str]:
    """Segment Japanese text into words.
    
    Args:
        text: Japanese text
        
    Returns:
        List of word segments
    """
    # TODO: Implement with fugashi (MeCab)
    # import fugashi
    # tagger = fugashi.Tagger()
    # return [w.surface for w in tagger(text)]
    return [text]  # Placeholder