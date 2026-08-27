"""Minimal terminal UI that displays synced lyrics one word at a time,
centered on screen, using block character art."""

from __future__ import annotations

import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.text import Text

from .font import FONT




def _make_text_glyph(ch: str) -> list[str]:
    """Create a 7-row block glyph for characters not in FONT.

    Renders the character large and centered, framed by block characters.
    """
    S = "\u2588"
    display = ch
    # Create a large centered representation (6 chars wide)
    glyph = [
        f" {S * 4} ",
        f"{S}    {S}",
        f"{S} {display} {S}".ljust(6)[:6],
        f"{S} {display} {S}".ljust(6)[:6],
        f"{S} {display} {S}".ljust(6)[:6],
        f"{S}    {S}",
        f" {S * 4} ",
    ]
    return glyph


_TYPOGRAPHIC_MAP = {
    "\u2018": "'",  # left single quote → straight
    "\u2019": "'",  # right single quote → straight
    "\u201c": "",  # left double quote → remove
    "\u201d": "",  # right double quote → remove
    "\u0022": "",  # straight double quote → remove
    "\u2013": "-",  # en dash → hyphen
    "\u2014": "-",  # em dash → hyphen
    "\u2026": "...",  # ellipsis → three dots
    "\u00b7": ".",  # middle dot → period
    "\u2022": "-",  # bullet → hyphen
    "\u00ab": "",  # left guillemet → remove
    "\u00bb": "",  # right guillemet → remove
    "\u2039": "'",  # single left guillemet → straight
    "\u203a": "'",  # single right guillemet → straight
    "(": "(",       # left parenthesis → keep
    ")": ")",       # right parenthesis → keep
}


def render_big(text: str, max_width: int) -> list[str]:
    for typo, plain in _TYPOGRAPHIC_MAP.items():
        text = text.replace(typo, plain)

    normalized = text.upper()

    glyphs: list[list[str]] = []
    for ch in normalized:
        if ch in FONT:
            glyphs.append(FONT[ch])
        elif ch.lower() in FONT:
            glyphs.append(FONT[ch.lower()])
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


def _count_real_words(words: list[str]) -> int:
    """Count words that contain at least one letter (exclude pure punctuation)."""
    import re
    return sum(1 for w in words if re.search(r'[a-zA-Záéíóúüñ]', w))


class TerminalUI:
    def __init__(self, offset_ms: int = 0, color: str = "bold white", word_count: int = 0) -> None:
        self.console = Console()
        self._live: Live | None = None
        self._prev_lyric_idx: int = -1
        self._word_index: int = 0
        self._word_change_time: float = time.monotonic()
        self._offset_ms = offset_ms
        self._color = color
        self._word_count = word_count  # 0 = auto mode

    def render(
        self,
        track: Any,
        lyrics: Any,
        fetching: bool = False,
    ) -> None:
        if self._live is None:
            self.console.clear()
            self._live = Live(
                self._build_frame(track, lyrics, fetching),
                console=self.console,
                refresh_per_second=20,
                vertical_overflow="visible",
                transient=True,
            )
            self._live.start()
        else:
            self._live.update(self._build_frame(track, lyrics, fetching))

    def stop(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None
        # Reset terminal state - show cursor
        self.console.show_cursor(True)
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
 
        if not hasattr(lyrics, 'get_effective_offset'):
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
        fetching: bool = False,
    ) -> Text:
        text = Text()

        width, height = self.console.size

        if lyrics is None or not lyrics or not hasattr(lyrics, 'lines'):
            # Show track info and "no lyrics" message instead of blank space
            if track:
                track_name = getattr(track, 'name', 'Unknown Track')
                track_artist = getattr(track, 'artists', 'Unknown Artist')
                track_album = getattr(track, 'album', '')
                
                # Center the text vertically
                empty_lines = (height - 5) // 2
                for _ in range(max(0, empty_lines)):
                    text.append("\n")
                
                text.append(f"  {track_name}\n", style="bold " + self._color)
                text.append(f"  {track_artist}\n", style=self._color)
                if track_album:
                    text.append(f"  {track_album}\n", style="dim " + self._color)
                text.append("\n", style=self._color)
                if fetching:
                    text.append("  \u25b8 Loading lyrics... \u25c0\n", style="cyan")
                else:
                    text.append("  \u25b8 No lyrics found \u25c0\n", style="yellow")
            else:
                empty_lines = (height - 1) // 2
                for _ in range(max(0, empty_lines)):
                    text.append("\n")
                text.append("  \u25b8 Waiting for Spotify... \u25c0\n", style="yellow")
            
            # Fill remaining lines
            current_lines = len(text.plain.split("\n")) - 1
            for _ in range(max(0, height - current_lines)):
                text.append("\n")
            return text

        lines = lyrics.lines
        is_synced = lyrics.is_synced
        progress_ms = track.progress_ms

        idx = self._get_current_lyric_index(lines, progress_ms, is_synced, lyrics)

        if idx < 0 or idx >= len(lines):
            for _ in range(height):
                text.append(" " * width + "\n", style=self._color)
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
        elif not is_synced or len(words) == 1:
            # Unsynced or single word: show full line at once
            big_lines = render_big(line_text, width - 4)
        else:
            real_count = _count_real_words(words)
            effective_count = self._word_count if self._word_count > 0 else min(3, real_count)

            if is_synced and idx + 1 < len(lines) and lines[idx + 1].start_ms is not None:
                line_duration = lines[idx + 1].start_ms - lines[idx].start_ms
            elif is_synced and lines[idx].end_ms is not None:
                line_duration = lines[idx].end_ms - lines[idx].start_ms
            else:
                line_duration = len(words) * 800

            word_duration_ms = max(300, line_duration // max(1, real_count))
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
                        self._word_index = (interpolated_idx // max(1, effective_count)) * effective_count
                    else:
                        now = time.monotonic()
                        if now - self._word_change_time >= word_duration_s:
                            self._word_index += max(1, effective_count)
                            self._word_change_time = now
                else:
                    now = time.monotonic()
                    if now - self._word_change_time >= word_duration_s:
                        self._word_index += max(1, effective_count)
                        self._word_change_time = now
            else:
                now = time.monotonic()
                if now - self._word_change_time >= word_duration_s:
                    self._word_index += max(1, effective_count)
                    self._word_change_time = now

            if self._word_index >= len(words):
                self._word_index = 0

            # Auto-resize: find largest N of complete words that fits the screen
            if self._word_count == 0:
                best_n = 1
                for n in range(min(6, len(words)), 0, -1):
                    end = min(self._word_index + n, len(words))
                    candidate = " ".join(words[self._word_index:end])
                    # Calculate raw width without truncation
                    typo_candidate = candidate
                    for typo, plain in _TYPOGRAPHIC_MAP.items():
                        typo_candidate = typo_candidate.replace(typo, plain)
                    glyph_count = len(typo_candidate.upper())
                    raw_w = glyph_count * 6 + max(0, glyph_count - 1)
                    if raw_w <= width - 4:
                        best_n = n
                        break
                effective_count = best_n

            end_idx = min(self._word_index + effective_count, len(words))
            display_text = " ".join(words[self._word_index:end_idx])
            big_lines = render_big(display_text, width - 4)

        total_height = len(big_lines)
        pad_top = max(0, (height - total_height) // 2)

        for _ in range(pad_top):
            text.append(" " * width + "\n", style=self._color)

        for line in big_lines:
            line_width = len(line)
            pad_left = max(0, (width - line_width) // 2)
            pad_right = max(0, width - pad_left - line_width)
            text.append(" " * pad_left + line + " " * pad_right + "\n", style=self._color)

        remaining = max(0, height - pad_top - total_height)
        for _ in range(remaining):
            text.append(" " * width + "\n", style=self._color)

        return text
