"""Minimal terminal UI that displays synced lyrics one word at a time,
centered on screen, using block character art."""

from __future__ import annotations

import os
import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.text import Text

from .font import FONT

# Japanese Hiragana → Romaji mapping
_HIRAGANA_TO_ROMAJI = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
    "きゃ": "kya", "きゅ": "kyu", "きょ": "kyo",
    "しゃ": "sha", "しゅ": "shu", "しょ": "sho",
    "ちゃ": "cha", "ちゅ": "chu", "ちょ": "cho",
    "にゃ": "nya", "にゅ": "nyu", "にょ": "nyo",
    "ひゃ": "hya", "ひゅ": "hyu", "ひょ": "hyo",
    "みゃ": "mya", "みゅ": "myu", "みょ": "myo",
    "りゃ": "rya", "りゅ": "ryu", "りょ": "ryo",
    "ぎゃ": "gya", "ぎゅ": "gyu", "ぎょ": "gyo",
    "じゃ": "ja", "じゅ": "ju", "じょ": "jo",
    "びゃ": "bya", "びゅ": "byu", "びょ": "byo",
    "ぴゃ": "pya", "ぴゅ": "pyu", "ぴょ": "pyo",
}

# Japanese Katakana → Romaji mapping
_KATAKANA_TO_ROMAJI = {
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o",
    "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke", "コ": "ko",
    "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so",
    "タ": "ta", "チ": "chi", "ツ": "tsu", "テ": "te", "ト": "to",
    "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho",
    "マ": "ma", "ミ": "mi", "ム": "mu", "メ": "me", "モ": "mo",
    "ヤ": "ya", "ユ": "yu", "ヨ": "yo",
    "ラ": "ra", "リ": "ri", "ル": "ru", "レ": "re", "ロ": "ro",
    "ワ": "wa", "ヲ": "wo", "ン": "n",
    "ガ": "ga", "ギ": "gi", "グ": "gu", "ゲ": "ge", "ゴ": "go",
    "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo",
    "ダ": "da", "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do",
    "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be", "ボ": "bo",
    "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po",
    "キャ": "kya", "キュ": "kyu", "キョ": "kyo",
    "シャ": "sha", "シュ": "shu", "ショ": "sho",
    "チャ": "cha", "チュ": "chu", "チョ": "cho",
    "ニャ": "nya", "ニュ": "nyu", "ニョ": "nyo",
    "ヒャ": "hya", "ヒュ": "hyu", "ヒョ": "hyo",
    "ミャ": "mya", "ミュ": "myu", "ミョ": "myo",
    "リャ": "rya", "リュ": "ryu", "リョ": "ryo",
    "ギャ": "gya", "ギュ": "gyu", "ギョ": "gyo",
    "ジャ": "ja", "ジュ": "ju", "ジョ": "jo",
    "ビャ": "bya", "ビュ": "byu", "ビョ": "byo",
    "ピャ": "pya", "ピュ": "pyu", "ピョ": "pyo",
    "ー": "",
}

# Common Kanji readings (single char)
_KANJI_TO_ROMAJI = {
    "愛": "ai", "音": "on", "歌": "uta", "泳": "oyogi",
    "駅": "eki", "夏": "natsu", "記": "ki", "琴": "koto",
    "空": "sora", "工": "kou", "口": "kuchi", "今": "ima",
    "魚": "sakana", "金": "kin", "語": "go", "午": "go",
    "後": "ato", "五": "go", "骨": "hone", "込": "komi",
    "左": "hidari", "散": "san", "詩": "shi", "歯": "ha",
    "四": "yon", "糸": "ito", "字": "ji", "耳": "mimi",
    "七": "nana", "辞": "ji", "写": "sha", "者": "sha",
    "主": "shu", "酒": "sake", "首": "kubi", "秋": "aki",
    "週": "shuu", "春": "haru", "書": "sho", "少": "shou",
    "場": "ba", "色": "iro", "心": "kokoro", "新": "shin",
    "图": "zu", "数": "suu", "西": "nishi", "声": "koe",
    "星": "hoshi", "晴": "hare", "切": "kiri", "雪": "yuki",
    "船": "fune", "先": "sen", "線": "sen", "前": "mae",
    "多": "ta", "太": "ta", "体": "tai", "地": "chi",
    "知": "chi", "茶": "cha", "昼": "hiru", "長": "naga",
    "鳥": "tori", "通": "tsuu", "典": "ten", "店": "ten",
    "点": "ten", "電": "den", "刀": "katana", "冬": "fuyu",
    "当": "tou", "東": "higashi", "答": "kotae", "同": "dou",
    "道": "michi", "読": "yomi", "内": "nai", "南": "minami",
    "肉": "niku", "馬": "uma", "売": "uri", "飯": "meshi",
    "日": "hi", "入": "iri", "猫": "neko", "北": "kita",
    "白": "shiro", "百": "hyaku", "文": "bun", "木": "ki",
    "本": "hon", "米": "kome", "毛": "ke", "門": "mon",
    "夜": "yoru", "野": "no", "来": "rai", "立": "tachi",
    "林": "hayashi", "六": "roku", "話": "hanashi",
}


def _to_romaji(text: str) -> str:
    """Convert Japanese text to romaji for block art rendering."""
    result = []
    i = 0
    while i < len(text):
        # Try 2-char combo first (e.g., きゃ, キャ)
        if i + 1 < len(text):
            pair = text[i:i+2]
            if pair in _HIRAGANA_TO_ROMAJI:
                result.append(_HIRAGANA_TO_ROMAJI[pair])
                i += 2
                continue
            if pair in _KATAKANA_TO_ROMAJI:
                result.append(_KATAKANA_TO_ROMAJI[pair])
                i += 2
                continue

        ch = text[i]
        if ch in _HIRAGANA_TO_ROMAJI:
            result.append(_HIRAGANA_TO_ROMAJI[ch])
        elif ch in _KATAKANA_TO_ROMAJI:
            result.append(_KATAKANA_TO_ROMAJI[ch])
        elif ch in _KANJI_TO_ROMAJI:
            result.append(_KANJI_TO_ROMAJI[ch])
        else:
            result.append(ch)
        i += 1

    return "".join(result)


def _make_text_glyph(ch: str) -> list[str]:
    """Create a 7-row block glyph for characters not in FONT.

    Renders the character large and centered, framed by block characters.
    """
    S = "\u2588"
    display = ch
    # Create a large centered representation
    glyph = [
        f" {S * 4} ",
        f"{S}    {S}",
        f"{S} {display} {S}",
        f"{S} {display} {S}",
        f"{S} {display} {S}",
        f"{S}    {S}",
        f" {S * 4} ",
    ]
    return glyph


def render_big(text: str, max_width: int) -> list[str]:
    # Convert Japanese to romaji first
    text = _to_romaji(text)

    normalized = text.upper()
    for ch in "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00fc":
        normalized = normalized.replace(ch.upper(), ch)

    glyphs: list[list[str]] = []
    for ch in normalized:
        if ch in FONT:
            glyphs.append(FONT[ch])
        else:
            glyphs.append(_make_text_glyph(ch))

    if not glyphs:
        return [""] * 7

    raw_width = len(glyphs) * 6 + max(0, len(glyphs) - 1)
    if raw_width == 0:
        return [""] * 7

    if raw_width > max_width:
        count = max(1, (max_width + 1) // 7)
        glyphs = glyphs[:count]

    rows: list[str] = []
    for r in range(7):
        parts = []
        for g_idx, glyph in enumerate(glyphs):
            parts.append(glyph[r])
            if g_idx < len(glyphs) - 1:
                parts.append(" ")
        rows.append("".join(parts))
    return rows


def _split_words(text: str) -> list[str]:
    """Split text into words, joining punctuation with adjacent words.

    Prevents punctuation marks from appearing as separate words.
    - Closure punctuation (?, !, ., ...) attaches to previous word: 'week ? hey' → 'week? hey'
    - Opening punctuation (¿, ¡) stays at start: '¿qué' → '¿qué'
    - If no previous word, closure punct attaches to next: '? Hello' → '?Hello'
    """
    raw = text.split()
    if not raw:
        return []

    closure = set("?!.,;:\u2026")
    opening = set("\u00bf\u00a1")

    result: list[str] = []
    pending = ""

    for word in raw:
        # Parse: opening prefix, core, trailing closure, leading closure
        leading_open = ""
        core = word
        while core and core[0] in opening:
            leading_open += core[0]
            core = core[1:]
        trailing = ""
        while core and core[-1] in closure:
            trailing = core[-1] + trailing
            core = core[:-1]
        leading_close = ""
        while core and core[0] in closure:
            leading_close += core[0]
            core = core[1:]

        if not core:
            # Pure punctuation token — accumulate
            pending += leading_open + leading_close + trailing
        else:
            # Word with punctuation attached
            word = leading_open + leading_close + core + trailing
            if pending:
                if result:
                    result[-1] += pending
                else:
                    word = pending + word
                pending = ""
            result.append(word)

    if pending and result:
        result[-1] += pending
    elif pending:
        result.append(pending)

    return result


class TerminalUI:
    def __init__(self, offset_ms: int = 0, color: str = "bold white") -> None:
        self.console = Console()
        self._live: Live | None = None
        self._prev_lyric_idx: int = -1
        self._word_index: int = 0
        self._word_change_time: float = time.monotonic()
        self._offset_ms = offset_ms
        self._color = color

    def render(
        self,
        track: Any,
        lyrics: Any,
    ) -> None:
        if self._live is None:
            self._live = Live(
                self._build_frame(track, lyrics),
                console=self.console,
                refresh_per_second=20,
            )
            self._live.start()
        else:
            self._live.update(self._build_frame(track, lyrics))

    def stop(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        self.console.clear()

    def print_error(self, msg: str) -> None:
        self.console.print(f"[red]\u2717[/red] {msg}")

    def print_info(self, msg: str) -> None:
        self.console.print(f"[blue]\u25b8[/blue] {msg}")

    def _get_current_lyric_index(
        self,
        lines: list[Any],
        progress_ms: int,
        is_synced: bool,
        lyrics: Any = None,
    ) -> int:
        if not lines:
            return -1

        if is_synced:
            offset = self._offset_ms
            if lyrics and hasattr(lyrics, 'get_effective_offset'):
                offset = lyrics.get_effective_offset()

            adjusted = progress_ms - offset
            idx = -1
            for i, line in enumerate(lines):
                # Add 200ms buffer: only show line when clearly past its start
                if line.start_ms is not None and line.start_ms <= adjusted - 200:
                    idx = i
                elif line.start_ms is not None and line.start_ms > adjusted - 200:
                    break
            return idx
        else:
            line_duration_ms = 5000
            idx = (progress_ms // line_duration_ms) % len(lines)
            return int(idx)

    def _build_frame(
        self,
        track: Any,
        lyrics: Any,
    ) -> Text:
        text = Text()

        try:
            term_size = os.get_terminal_size()
            width = term_size.columns
            height = term_size.lines
        except (ValueError, OSError):
            width, height = 80, 24

        if lyrics is None or not lyrics:
            pad = (height - 7) // 2
            text.append("\n" * pad, style=self._color)
            text.append(" " * ((width - 3) // 2) + "...", style=self._color)
            text.append("\n" * (height - pad - 1), style=self._color)
            return text

        lines = lyrics.lines
        is_synced = lyrics.is_synced
        progress_ms = track.progress_ms

        idx = self._get_current_lyric_index(lines, progress_ms, is_synced, lyrics)

        if idx < 0 or idx >= len(lines):
            # No active lyric - show empty space
            text.append("\n" * height, style=self._color)
            return text

        line_text = lines[idx].text

        if idx != self._prev_lyric_idx:
            self._prev_lyric_idx = idx
            self._word_index = 0
            self._word_change_time = time.monotonic()

        has_spaces = " " in line_text
        if has_spaces:
            words = _split_words(line_text)
        else:
            words = list(line_text)

        if not words:
            big_lines = [""] * 7
        elif len(words) == 1:
            big_lines = render_big(words[0], width - 4)
        else:
            if is_synced and idx + 1 < len(lines) and lines[idx + 1].start_ms is not None:
                line_duration = lines[idx + 1].start_ms - lines[idx].start_ms
            elif is_synced and lines[idx].end_ms is not None:
                line_duration = lines[idx].end_ms - lines[idx].start_ms
            else:
                line_duration = len(words) * 800

            word_duration_ms = max(300, line_duration // len(words))
            word_duration_s = word_duration_ms / 1000.0

            if is_synced:
                offset = self._offset_ms
                if lyrics and hasattr(lyrics, 'get_effective_offset'):
                    offset = lyrics.get_effective_offset()

                adjusted = progress_ms - offset
                current_line = lines[idx]
                if current_line.start_ms is not None and current_line.end_ms is not None:
                    duration = current_line.end_ms - current_line.start_ms
                    if duration > 0:
                        # Add 100ms buffer before first word appears
                        elapsed = adjusted - current_line.start_ms - 100
                        ratio = max(0.0, min(1.0, elapsed / duration))
                        interpolated_idx = min(int(ratio * len(words)), len(words) - 1)
                        self._word_index = interpolated_idx
                    else:
                        now = time.monotonic()
                        if now - self._word_change_time >= word_duration_s:
                            self._word_index += 1
                            self._word_change_time = now
                else:
                    now = time.monotonic()
                    if now - self._word_change_time >= word_duration_s:
                        self._word_index += 1
                        self._word_change_time = now
            else:
                now = time.monotonic()
                if now - self._word_change_time >= word_duration_s:
                    self._word_index += 1
                    self._word_change_time = now

            if self._word_index >= len(words):
                self._word_index = 0

            big_lines = render_big(words[self._word_index], width - 4)

        total_height = len(big_lines)
        pad_top = max(0, (height - total_height) // 2)

        text.append("\n" * pad_top, style=self._color)

        for line in big_lines:
            line_width = len(line)
            pad_left = max(0, (width - line_width) // 2)
            text.append(" " * pad_left + line + "\n", style=self._color)

        remaining = height - pad_top - total_height - 1
        if remaining > 0:
            text.append("\n" * remaining, style=self._color)

        return text
