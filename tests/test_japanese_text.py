"""Tests for Japanese text processing module."""

import pytest
from src.japanese_text import (
    is_hiragana,
    is_katakana,
    is_kanji,
    is_japanese,
    normalize_japanese,
    has_japanese,
    count_japanese_chars,
    to_hiragana,
    to_katakana,
    normalize_japanese,
    JapaneseMode,
    convert_japanese_mode,
)


class TestJapaneseCharDetection:
    """Tests for Japanese character detection."""

    def test_is_hiragana(self):
        assert is_hiragana("あ") is True
        assert is_hiragana("い") is True
        assert is_hiragana("ア") is False
        assert is_hiragana("漢") is False
        assert is_hiragana("a") is False
        assert is_hiragana("") is False

    def test_is_katakana(self):
        assert is_katakana("ア") is True
        assert is_katakana("イ") is True
        assert is_katakana("あ") is False
        assert is_katakana("漢") is False
        assert is_katakana("a") is False

    def test_is_kanji(self):
        assert is_kanji("漢") is True
        assert is_kanji("字") is True
        assert is_kanji("あ") is False
        assert is_kanji("ア") is False
        assert is_kanji("a") is False

    def test_is_japanese(self):
        assert is_japanese("あ") is True
        assert is_japanese("ア") is True
        assert is_japanese("漢") is True
        assert is_japanese("a") is False
        assert is_japanese("1") is False
        assert is_japanese("") is False


class TestJapaneseTextNormalization:
    """Tests for Japanese text normalization."""

    def test_normalize_fullwidth_ascii(self):
        text = "Ｈｅｌｌｏ　Ｗｏｒｌｄ"
        normalized = normalize_japanese(text)
        assert normalized == "Hello World"

    def test_normalize_wave_dash(self):
        text = "Hello～World"  # Full-width tilde U+FF5E
        normalized = normalize_japanese(text)
        assert normalized == "HelloーWorld"

    def test_nfkc_normalization(self):
        text = "ﾋﾗｶﾞﾅ"  # Half-width katakana
        normalized = normalize_japanese(text)
        assert normalized == "ヒラガナ"


class TestJapaneseTextDetection:
    """Tests for Japanese text detection utilities."""

    def test_has_japanese(self):
        assert has_japanese("Hello あ World") is True
        assert has_japanese("Hello World") is False
        assert has_japanese("") is False

    def test_count_japanese_chars(self):
        counts = count_japanese_chars("あア漢a1")
        assert counts == {"hiragana": 1, "katakana": 1, "kanji": 1, "other": 2}

    def test_count_only_kanji(self):
        counts = count_japanese_chars("漢字")
        assert counts == {"hiragana": 0, "katakana": 0, "kanji": 2, "other": 0}

    def test_count_only_hiragana(self):
        counts = count_japanese_chars("あいうえお")
        assert counts == {"hiragana": 5, "katakana": 0, "kanji": 0, "other": 0}

    def test_count_only_katakana(self):
        counts = count_japanese_chars("アイウエオ")
        assert counts == {"hiragana": 0, "katakana": 5, "kanji": 0, "other": 0}


class TestScriptConversion:
    """Tests for script conversion functions."""

    def test_to_hiragana(self):
        assert to_hiragana("アイウエオ") == "あいうえお"
        assert to_hiragana("カキクケコ") == "かきくけこ"
        assert to_hiragana("あいうえお") == "あいうえお"  # Already hiragana

    def test_to_katakana(self):
        assert to_katakana("あいうえお") == "アイウエオ"
        assert to_katakana("かきくけこ") == "カキクケコ"
        assert to_katakana("アイウエオ") == "アイウエオ"  # Already katakana

    def test_convert_mixed_placeholder(self):
        # Currently just returns input as-is (placeholder)
        result = convert_japanese_mode("明日も晴れる", "mixed")
        assert result == "明日も晴れる"

    def test_convert_to_romaji_placeholder(self):
        # Currently just returns input as-is (placeholder)
        result = convert_japanese_mode("明日", "romaji")
        assert result == "明日"


class TestJapaneseMode:
    """Tests for JapaneseMode enum."""

    def test_mode_values(self):
        assert JapaneseMode.ROMAJI == "romaji"
        assert JapaneseMode.HIRAGANA == "hiragana"
        assert JapaneseMode.KATAKANA == "katakana"
        assert JapaneseMode.MIXED == "mixed"
        assert JapaneseMode.AUTO == "auto"


class TestJapaneseCharCounts:
    """Tests for counting Japanese characters."""

    def test_mixed_text(self):
        counts = count_japanese_chars("Hello あ World ア 漢")
        assert counts["hiragana"] == 1
        assert counts["katakana"] == 1
        assert counts["kanji"] == 1
        assert counts["other"] >= 3  # H, e, l, l, o, etc.

    def test_no_japanese(self):
        counts = count_japanese_chars("Hello World 123")
        assert counts == {"hiragana": 0, "katakana": 0, "kanji": 0, "other": 15}