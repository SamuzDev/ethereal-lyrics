"""Tests for terminal_ui module."""

import pytest
from src.terminal_ui import (
    _split_words,
    _count_real_words,
    render_big,
    _make_text_glyph,
    _TYPOGRAPHIC_MAP,
)


class TestSplitWords:
    """Tests for _split_words function."""

    def test_simple_words(self):
        words = _split_words("Rise and shine")
        assert words == ["Rise", "and", "shine"]

    def test_parentheses_attached(self):
        words = _split_words("Rise and shine (Rise and shine)")
        assert words == ["Rise", "and", "shine", "(Rise", "and", "shine)"]

    def test_pure_punctuation(self):
        words = _split_words("... ... ...")
        assert words == ["........."]

    def test_mixed_punctuation(self):
        words = _split_words("Hello ... World!")
        assert words == ["Hello...", "World!"]

    def test_ellipsis_attachment(self):
        words = _split_words("Look at me now...")
        assert words == ["Look", "at", "me", "now..."]

    def test_opening_punctuation(self):
        words = _split_words("¿Qué tal?")
        assert words == ["¿Qué", "tal?"]

    def test_multiple_closure(self):
        words = _split_words("Really??! No way...")
        assert words == ["Really??!", "No", "way..."]


class TestCountRealWords:
    """Tests for _count_real_words function."""

    def test_normal_words(self):
        words = ["Rise", "and", "shine"]
        assert _count_real_words(words) == 3

    def test_with_punctuation_tokens(self):
        words = ["Rise", "and", "shine", "(Rise", "and", "shine)"]
        assert _count_real_words(words) == 6

    def test_pure_punctuation(self):
        words = ["........."]
        assert _count_real_words(words) == 0

    def test_mixed(self):
        words = ["Hello...", "World!"]
        assert _count_real_words(words) == 2

    def test_empty_list(self):
        words = []
        assert _count_real_words(words) == 0

    def test_only_punctuation(self):
        words = ["...", "!!!", "???"]
        assert _count_real_words(words) == 0


class TestRenderBig:
    """Tests for render_big function."""

    def test_single_word(self):
        result = render_big("HELLO", 80)
        assert len(result) == 7
        assert all(len(line) > 0 for line in result)

    def test_multiple_words(self):
        result = render_big("HELLO WORLD", 80)
        assert len(result) == 7

    def test_empty_string(self):
        result = render_big("", 80)
        assert result == [""] * 7

    def test_typographic_map(self):
        result = render_big("Hello…", 80)
        result2 = render_big("Hello...", 80)
        assert result == result2

    def test_parenthesis_rendering(self):
        result = render_big("(HELLO)", 80)
        assert len(result) == 7
        assert all(len(line) > 0 for line in result)


class TestMakeTextGlyph:
    """Tests for _make_text_glyph function."""

    def test_unknown_character(self):
        glyph = _make_text_glyph("@")
        assert len(glyph) == 7
        assert all(len(line) == 6 for line in glyph)

    def test_digit_character(self):
        glyph = _make_text_glyph("5")
        assert len(glyph) == 7


class TestTypographicMap:
    """Tests for _TYPOGRAPHIC_MAP constant."""

    def test_ellipsis_to_dots(self):
        assert _TYPOGRAPHIC_MAP["\u2026"] == "..."

    def test_quotes_removed(self):
        assert _TYPOGRAPHIC_MAP["\u201c"] == ""
        assert _TYPOGRAPHIC_MAP["\u201d"] == ""
        assert _TYPOGRAPHIC_MAP["\u0022"] == ""

    def test_dashes_to_hyphen(self):
        assert _TYPOGRAPHIC_MAP["\u2013"] == "-"
        assert _TYPOGRAPHIC_MAP["\u2014"] == "-"

    def test_parenthesis_removed(self):
        # Parentheses are now kept and rendered as block art
        assert _TYPOGRAPHIC_MAP["("] == "("
        assert _TYPOGRAPHIC_MAP[")"] == ")"