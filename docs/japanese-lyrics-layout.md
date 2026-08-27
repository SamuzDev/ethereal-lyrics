# Japanese Lyrics Layout Design

## Overview
Design document for Japanese lyrics rendering in ethereal-lyrics. Not yet implemented.

## Font Requirements

### Hiragana (平仮名) - 46 basic + 25 dakuon/handakuon + 33 yōon = 104 chars
| Char | Romaji | Glyph Size |
|------|--------|------------|
| あ | a | 6x7 |
| い | i | 6x7 |
| う | u | 6x7 |
| え | e | 6x7 |
| お | o | 6x7 |
| か | ka | 6x7 |
| が | ga | 6x7 |
| き | ki | 6x7 |
| ぎ | gi | 6x7 |
| ... | ... | ... |
| ん | n | 6x7 |

### Katakana (片仮名) - 46 basic + 25 dakuon/handakuon + 33 yōon = 104 chars
| Char | Romaji | Glyph Size |
|------|--------|------------|
| ア | a | 6x7 |
| イ | i | 6x7 |
| ウ | u | 6x7 |
| エ | e | 6x7 |
| オ | o | 6x7 |
| カ | ka | 6x7 |
| ガ | ga | 6x7 |
| ... | ... | ... |
| ン | n | 6x7 |

### Kanji (漢字) - Common lyrics kanji
- Top 500-1000 most common in Japanese lyrics
- Fallback to romaji/hiragana if not in font

## Layout Options

### Option 1: Romaji Only (Current fallback)
- Convert Japanese → romaji using pykakasi
- Render with existing Latin font
- Simple but loses Japanese aesthetic

### Option 2: Hiragana/Katakana Block Font
- Add hiragana/katakana glyphs to `font.py`
- ~208 new glyphs (104 hiragana + 104 katakana)
- Each glyph 6x7 block characters
- Render directly as block art

### Option 3: Mixed Script
- Kanji → fallback to hiragana/romaji
- Hiragana/katakana → block art
- Latin chars → existing font

## Font File Structure

```
src/
├── font.py           # Current Latin + symbols
├── font_hiragana.py  # Hiragana glyphs (new)
├── font_katakana.py  # Katakana glyphs (new)
├── font_kanji.py     # Common kanji (optional, large)
└── font_loader.py    # Unified loader (new)
```

## Rendering Pipeline

```
Japanese Lyrics Text
        │
        ▼
┌───────────────────┐
│ Text Normalization │
│ - NFKC normalize  │
│ - Remove variants │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ Script Detection  │
│ - Hiragana       │
│ - Katakana       │
│ - Kanji          │
│ - Latin          │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ Font Selection    │
│ - Hiragana → hira │
│ - Katakana → kata │
│ - Kanji → hira/rom│
│ - Latin → latin   │
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ Render Block Art  │
│ - 6x7 per char    │
│ - Center align    │
└───────────────────┘
```

## Japanese Word Segmentation

Unlike English, Japanese has no spaces. Need segmentation:

```python
# Use fugashi (MeCab wrapper) or nagisa
import fugashi
tagger = fugashi.Tagger()
words = [w.surface for w in tagger(text)]
# "明日も晴れるかな" → ["明日", "も", "晴れる", "かな"]
```

## Romaji Conversion (Fallback)

```python
import pykakasi
kks = pykakasi.kakasi()
result = kks.convert("明日も晴れるかな")
# [{"hira": "あした", "hepburn": "ashita", "orig": "明日"}, ...]
romaji = " ".join([r["hepburn"] for r in result])
# "ashita mo hareru kana"
```

## Configuration

```python
# config.py additions
japanese_mode: Literal["romaji", "hiragana", "katakana", "mixed"] = "mixed"
kanji_fallback: Literal["hiragana", "romaji"] = "hiragana"
show_romaji_below: bool = False  # Show romaji under Japanese
```

## Glyph Design Guidelines

### 6x7 Grid per Character
```
Row 0:  ████  
Row 1: █    █
Row 2: █ ●  █  ← character centered
Row 3: █ ●  █
Row 4: █ ●  █
Row 5: █    █
Row 6:  ████  
```

### Hiragana Examples (6x7)

**あ (a)**:
```
 █████ 
██   ██
██ ██ ██
████████
██ ██ ██
██   ██
 █████ 
```

**か (ka)**:
```
  ████  
 ██  ██
██   ██
 ██████
██   ██
██   ██
 ██████
```

## Implementation Phases

### Phase 1: Romaji Fallback (Week 1)
- Add pykakasi dependency
- Convert Japanese → romaji in lyrics fetcher
- Use existing Latin font

### Phase 2: Hiragana Font (Week 2-3)
- Design 104 hiragana glyphs
- Add to `font_hiragana.py`
- Integrate with renderer

### Phase 3: Katakana Font (Week 3-4)
- Design 104 katakana glyphs  
- Add to `font_katakana.py`

### Phase 4: Mixed Mode + Kanji (Week 4-5)
- Add fugashi for segmentation
- Kanji → hiragana fallback
- Mixed script rendering

## Dependencies to Add

```toml
[project.optional-dependencies]
japanese = [
    "pykakasi>=2.0",      # Romaji conversion
    "fugashi>=1.3",       # Japanese segmentation
    "unidic-lite>=1.0",   # MeCab dictionary
]
```

## Testing

```python
def test_japanese_rendering():
    # Test hiragana
    assert render_big("あいうえお", 80) == expected_hiragana
    
    # Test katakana
    assert render_big("アイウエオ", 80) == expected_katakana
    
    # Test mixed
    assert render_big("明日も晴れる", 80) == expected_mixed
    
    # Test romaji fallback
    with config(japanese_mode="romaji"):
        assert render_big("明日", 80) == render_big("ashita", 80)
```

## Files to Create

```
docs/japanese-lyrics-layout.md     # This file
src/font_hiragana.py               # Hiragana glyphs
src/font_katakana.py               # Katakana glyphs
src/font_loader.py                 # Unified font loader
src/japanese_text.py               # Segmentation + romaji
tests/test_japanese_rendering.py   # Tests
```

## Notes

- Total new glyphs: ~208 (hiragana + katakana)
- Font file size increase: ~208 * 7 * 6 ≈ 8.7KB
- Memory: negligible
- Rendering performance: same as Latin
- Start with romaji fallback (Phase 1) for quick win