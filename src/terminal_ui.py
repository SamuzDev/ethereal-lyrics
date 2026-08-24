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


def render_big(text: str, max_width: int) -> list[str]:
    normalized = text.upper()
    for ch in "\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1\u00fc":
        normalized = normalized.replace(ch.upper(), ch)

    glyphs: list[list[str]] = []
    for ch in normalized:
        if ch in FONT:
            glyphs.append(FONT[ch])
        else:
            glyphs.append(FONT.get("?", FONT[" "]))

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
