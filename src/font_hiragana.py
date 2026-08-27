"""Hiragana block character font definitions for Japanese lyrics.

This file contains block character glyphs for hiragana characters.
Each glyph is 6 characters wide x 7 rows tall.
Not yet implemented - design document only.
"""

from __future__ import annotations
from src.font import g


# Hiragana glyphs (104 characters: 46 basic + 25 dakuon/handakuon + 33 yōon)
# Format: "hiragana_char": g(row1, row2, ..., row7)
# Each row is 6 chars wide

HIRAGANA_FONT: dict[str, list[str]] = {
    # Basic hiragana (46)
    # "あ": g(...),  # TODO: implement
    # "い": g(...),
    # "う": g(...),
    # "え": g(...),
    # "お": g(...),
    # ...
    
    # Dakuon (voiced) - 20
    # "が": g(...),  # ga
    # "ぎ": g(...),  # gi
    # "ぐ": g(...),  # gu
    # "げ": g(...),  # ge
    # "ご": g(...),  # go
    # ...
    
    # Handakuon (semi-voiced) - 5
    # "ぱ": g(...),  # pa
    # "ぴ": g(...),  # pi
    # "ぷ": g(...),  # pu
    # "ぺ": g(...),  # pe
    # "ぽ": g(...),  # po
    
    # Yōon (combined) - 33
    # "きゃ": g(...),  # kya
    # "きゅ": g(...),  # kyu
    # "きょ": g(...),  # kyo
    # ...
    
    # Small chars
    # "っ": g(...),   # small tsu
    # "ゃ": g(...),   # small ya
    # "ゅ": g(...),   # small yu
    # "ょ": g(...),   # small yo
}

# Total: 104 hiragana characters
# Each glyph: 6 chars wide x 7 rows = 42 chars per glyph
# Total size: 104 * 42 = ~4.4KB