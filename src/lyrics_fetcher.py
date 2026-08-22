"""Lyrics fetcher using LRCLib API (free, synced lyrics support)."""

import httpx
from dataclasses import dataclass
from typing import Optional
from difflib import SequenceMatcher


@dataclass
class LyricLine:
    """Represents a single line of lyrics with optional timestamp."""

    text: str
    start_ms: Optional[int] = None  # None = unsynced line
    end_ms: Optional[int] = None


@dataclass
class Lyrics:
    """Represents fetched lyrics for a track."""

    track_name: str
    artist_name: str
    album_name: Optional[str]
    lines: list[LyricLine]
    is_synced: bool

    def __bool__(self) -> bool:
        """Check if lyrics are available."""
        return len(self.lines) > 0


class LyricsFetcher:
    """Fetches lyrics from LRCLib API."""

    def __init__(self, base_url: str = "https://lrclib.net/api"):
        """Initialize lyrics fetcher."""
        self.base_url = base_url
        self.client = httpx.Client(
            timeout=10.0,
            headers={"User-Agent": "ethereal-lyrics/0.1.0"},
        )
        self._cache: dict[str, Lyrics] = {}

    def _normalize(self, text: str) -> str:
        """Normalize text for fuzzy matching."""
        return text.lower().strip()

    def _fuzzy_match(self, a: str, b: str, threshold: float = 0.6) -> bool:
        """Check if two strings are similar enough."""
        return SequenceMatcher(None, self._normalize(a), self._normalize(b)).ratio() >= threshold

    def _parse_synced_lyrics(self, synced: str) -> list[LyricLine]:
        """Parse LRC format synced lyrics into LyricLine objects."""
        lines = []
        for raw_line in synced.strip().split("\n"):
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            # Parse timestamp format: [MM:SS.xx]
            if raw_line.startswith("["):
                bracket_end = raw_line.find("]")
                if bracket_end == -1:
                    continue

                timestamp = raw_line[1:bracket_end]
                text = raw_line[bracket_end + 1:].strip()

                # Parse MM:SS.xx format
                try:
                    parts = timestamp.split(":")
                    minutes = int(parts[0])
                    sec_parts = parts[1].split(".")
                    seconds = int(sec_parts[0])
                    centiseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
                    start_ms = (minutes * 60 + seconds) * 1000 + centiseconds * 10
                    lines.append(LyricLine(text=text, start_ms=start_ms))
                except (ValueError, IndexError):
                    continue

        # Calculate end_ms for each line
        for i in range(len(lines)):
            if i + 1 < len(lines):
                lines[i].end_ms = lines[i + 1].start_ms
            else:
                lines[i].end_ms = lines[i].start_ms + 5000  # Last line gets 5s

        return lines

    def _parse_plain_lyrics(self, plain: str) -> list[LyricLine]:
        """Parse plain text lyrics into unsynced LyricLine objects."""
        lines = []
        for raw_line in plain.strip().split("\n"):
            text = raw_line.strip()
            if text:
                lines.append(LyricLine(text=text))
        return lines

    def fetch_lyrics(
        self,
        track_name: str,
        artist_name: str,
        album_name: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> Optional[Lyrics]:
        """Fetch lyrics for a track.

        Tries to get synced lyrics first, falls back to plain lyrics.
        Uses fuzzy matching for better results.
        """
        cache_key = f"{artist_name}:{track_name}".lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Try exact search first
            response = self.client.get(
                f"{self.base_url}/get",
                params={
                    "track_name": track_name,
                    "artist_name": artist_name,
                    "album_name": album_name or "",
                    "duration": duration_ms // 1000 if duration_ms else None,
                },
            )

            if response.status_code == 200:
                data = response.json()
                result = self._parse_response(data, track_name, artist_name, album_name)
                if result:
                    self._cache[cache_key] = result
                    return result

            # Fuzzy search fallback
            response = self.client.get(
                f"{self.base_url}/search",
                params={
                    "track_name": track_name,
                    "artist_name": artist_name,
                    "album_name": album_name or "",
                },
            )

            if response.status_code == 200:
                results = response.json()
                for item in results:
                    if self._fuzzy_match(item.get("trackName", ""), track_name):
                        result = self._parse_response(
                            item, track_name, artist_name, album_name
                        )
                        if result:
                            self._cache[cache_key] = result
                            return result

        except httpx.HTTPError:
            return None

        return None

    def _parse_response(
        self,
        data: dict,
        track_name: str,
        artist_name: str,
        album_name: Optional[str],
    ) -> Optional[Lyrics]:
        """Parse API response into Lyrics object."""
        synced = data.get("syncedLyrics")
        plain = data.get("plainLyrics")

        lines = []
        is_synced = False

        if synced:
            lines = self._parse_synced_lyrics(synced)
            is_synced = True
        elif plain:
            lines = self._parse_plain_lyrics(plain)

        if not lines:
            return None

        return Lyrics(
            track_name=data.get("trackName", track_name),
            artist_name=data.get("artistName", artist_name),
            album_name=data.get("albumName", album_name),
            lines=lines,
            is_synced=is_synced,
        )
