"""Katakana block character font definitions for Japanese lyrics.

This file contains block character glyphs for katakana characters.
Each glyph is 6 characters wide x 7 rows tall.
Not yet implemented - design document only.
"""

from __future__ import annotations
from src.font import g


# Katakana glyphs (104 characters: 46 basic + 25 dakuon/handakuon + 33 yōon)
# Format: "katakana_char": g(row1, row2, ..., row7)
# Each row is 6 chars wide

KATAKANA_FONT: dict[str, list[str]] = {
    # Basic katakana (46)
    # "ア": g(...),  # TODO: implement
    # "イ": g(...),
    # "ウ": g(...),
    # "エ": g(...),
    # "オ": g(...),
    # ...
    
    # Dakuon (voiced) - 20
    # "ガ": g(...),  # ga
    # "ギ": g(...),  # gi
    # "グ": g(...),  # gu
    # "ゲ": g(...),  # ge
    # "ゴ": g(...),  # go
    # ...
    
    # Handakuon (semi-voiced) - 5
    # "パ": g(...),  # pa
    # "ピ": g(...),  # pi
    # "プ": g(...),  # pu
    # "ペ": g(...),  # pe
    # "ポ": g(...),  # po
    
    # Yōon (combined) - 33
    # "キャ": g(...),  # kya
    # "キュ": g(...),  # kyu
    # "キョ": g(...),  # kyo
    # ...
    
    # Small chars
    # "ッ": g(...),   # small tsu
    # "ャ": g(...),   # small ya
    # "ュ": g(...),   # small yu
    # "ョ": g(...),   # small yo
    # "ー": g(...),   # chōon (long vowel)
}

# Total: 104 katakana characters
# Each glyph: 6 chars wide x 7 rows = 42 chars per glyph
# Total size: 104 * 42 = ~4.4KB