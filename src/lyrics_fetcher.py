"""Multi-provider lyrics fetcher with fallback support.

Providers:
- LRCLib: Free, synced lyrics, no auth required
- Musixmatch: High quality synced lyrics, requires API key (free tier: 2000/day)
"""

import httpx
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from abc import ABC, abstractmethod


def parse_synced_lyrics(synced: str) -> list["LyricLine"]:
    """Parse LRC format synced lyrics into LyricLine objects."""
    lines = []
    for raw_line in synced.strip().split("\n"):
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        if raw_line.startswith("["):
            bracket_end = raw_line.find("]")
            if bracket_end == -1:
                continue

            timestamp = raw_line[1:bracket_end]
            text = raw_line[bracket_end + 1:].strip()

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

    for i in range(len(lines)):
        if i + 1 < len(lines):
            lines[i].end_ms = lines[i + 1].start_ms
        else:
            lines[i].end_ms = lines[i].start_ms + 5000

    return lines


def parse_plain_lyrics(plain: str) -> list["LyricLine"]:
    """Parse plain text lyrics into LyricLine objects."""
    lines = []
    for raw_line in plain.strip().split("\n"):
        text = raw_line.strip()
        if text:
            lines.append(LyricLine(text=text))
    return lines


@dataclass
class DynamicOffset:
    """Calculates dynamic offset based on playback timing.

    Tracks the drift between expected position and Spotify's reported position
    to automatically sync lyrics. Also detects speed changes (like fast rap)
    and adjusts offset accordingly.
    """

    _samples: list[tuple[float, int]] = field(default_factory=list)
    _track_start_time: float = 0.0
    _last_track_id: str = ""
    _calibrated_offset: int = 0
    _min_samples: int = 3
    _max_samples: int = 15

    _speed_history: list[float] = field(default_factory=list)
    _max_speed_history: int = 8
    _baseline_speed: float = 1.0
    _speed_adjustment: int = 0
    _smoothing_factor: float = 0.3

    def reset(self, track_id: str = "") -> None:
        """Reset calibration for a new track."""
        if track_id != self._last_track_id:
            self._samples.clear()
            self._speed_history.clear()
            self._track_start_time = time.monotonic()
            self._last_track_id = track_id
            self._calibrated_offset = 0
            self._speed_adjustment = 0
            self._baseline_speed = 1.0

    def add_sample(self, position_ms: int) -> None:
        """Add a timing sample from Spotify."""
        now = time.monotonic()
        self._samples.append((now, position_ms))

        # Keep only recent samples
        if len(self._samples) > self._max_samples:
            self._samples = self._samples[-self._max_samples:]

        # Calculate instantaneous speed
        if len(self._samples) >= 2:
            t_prev, pos_prev = self._samples[-2]
            t_curr, pos_curr = self._samples[-1]
            dt_real = (t_curr - t_prev) * 1000  # Convert to ms
            dt_position = pos_curr - pos_prev

            if dt_real > 0:
                # Speed: how many ms of song position per ms of real time
                # 1.0 = normal speed, >1.0 = faster than realtime
                speed = dt_position / dt_real
                self._speed_history.append(speed)

                if len(self._speed_history) > self._max_speed_history:
                    self._speed_history = self._speed_history[-self._max_speed_history:]

    def _calculate_speed_adjustment(self) -> int:
        """Calculate offset adjustment based on speed changes.

        When speed increases (fast rap), lyrics should appear earlier (negative offset).
        When speed decreases (slow part), lyrics should appear later (positive offset).
        """
        if len(self._speed_history) < 3:
            return 0

        # Calculate average speed and recent speed
        avg_speed = sum(self._speed_history) / len(self._speed_history)

        # Use last few samples for recent speed (more responsive)
        recent_samples = self._speed_history[-3:]
        recent_speed = sum(recent_samples) / len(recent_samples)

        # Detect if we're in a fast part (speed > 15% above baseline)
        speed_ratio = recent_speed / max(self._baseline_speed, 0.5)

        if speed_ratio > 1.15:
            # Fast part detected - show lyrics earlier
            # The faster the rap, the more negative the adjustment
            adjustment = int((1.0 - speed_ratio) * 200)  # -30ms for 15% faster, -100ms for 50% faster
            adjustment = max(adjustment, -150)  # Cap at -150ms
        elif speed_ratio < 0.85:
            # Slow part - show lyrics later
            adjustment = int((1.0 - speed_ratio) * 100)  # Positive adjustment
            adjustment = min(adjustment, 100)  # Cap at +100ms
        else:
            # Normal speed - no adjustment
            adjustment = 0

        # Smooth the adjustment
        self._speed_adjustment = int(
            self._speed_adjustment * 0.7 + adjustment * 0.3
        )

        return self._speed_adjustment

    def calculate_offset(self) -> int:
        """Calculate the dynamic offset based on timing drift and speed.

        Returns offset in milliseconds. Negative = lyrics should appear earlier.
        """
        if len(self._samples) < self._min_samples:
            return 0

        n = len(self._samples)
        if n < 2:
            return 0

        # Calculate expected vs actual positions (drift)
        t0, pos0 = self._samples[0]
        total_time_ms = (self._samples[-1][0] - t0) * 1000
        total_position_ms = self._samples[-1][1] - pos0

        if total_time_ms <= 0:
            return 0

        # Drift rate: how much Spotify's position differs from real time
        drift_rate = (total_position_ms / total_time_ms) - 1.0

        # Calculate average offset from drift
        avg_drift_ms = int(drift_rate * total_time_ms * 0.1)

        # Get speed-based adjustment
        speed_adj = self._calculate_speed_adjustment()

        # Combine drift and speed adjustments
        combined = int(avg_drift_ms * 0.6 + speed_adj * 0.4)

        # Smooth the final offset
        self._calibrated_offset = int(
            self._calibrated_offset * 0.7 + combined * 0.3
        )

        return self._calibrated_offset

    def get_confidence(self) -> float:
        """Get confidence in the calibration (0.0 to 1.0)."""
        if len(self._samples) < self._min_samples:
            return 0.0
        return min(1.0, len(self._samples) / self._max_samples)

    def get_current_speed(self) -> float:
        """Get current playback speed ratio (1.0 = normal)."""
        if not self._speed_history:
            return 1.0
        return self._speed_history[-1]


@dataclass
class LyricLine:
    """Represents a single line of lyrics with optional timestamp."""

    text: str
    start_ms: int | None = None
    end_ms: int | None = None
    _duration_ms: int | None = None
    _words: list[str] | None = None
    _word_positions: list[tuple[int, int]] | None = None


@dataclass
class Lyrics:
    """Represents fetched lyrics for a track."""

    track_name: str
    artist_name: str
    album_name: str | None
    lines: list[LyricLine]
    is_synced: bool
    offset_ms: int = 0
    provider: str = "unknown"
    _dynamic_offset: DynamicOffset | None = field(default=None, repr=False)

    def __bool__(self) -> bool:
        return len(self.lines) > 0

    def get_effective_offset(self) -> int:
        """Get the effective offset combining static and dynamic offsets."""
        dynamic = 0
        if self._dynamic_offset:
            dynamic = self._dynamic_offset.calculate_offset()
        return self.offset_ms + dynamic

    def get_current_index(self, progress_ms: int) -> int:
        if not self.is_synced or not self.lines:
            return -1

        adjusted_ms = progress_ms - self.get_effective_offset()

        for i, line in enumerate(self.lines):
            if line.start_ms is None:
                continue
            if i + 1 < len(self.lines):
                next_line = self.lines[i + 1]
                if next_line.start_ms is not None:
                    if line.start_ms <= adjusted_ms < next_line.start_ms:
                        return i
                else:
                    if line.start_ms <= adjusted_ms:
                        return i
            else:
                if line.start_ms <= adjusted_ms:
                    return i
        return -1

    def get_interpolated_position(self, progress_ms: int) -> float:
        if not self.is_synced or not self.lines:
            return 0.0

        adjusted_ms = progress_ms - self.get_effective_offset()
        current_idx = self.get_current_index(progress_ms)

        if current_idx < 0:
            return 0.0

        current_line = self.lines[current_idx]
        if current_line.start_ms is None or current_line.end_ms is None:
            return 0.0

        duration = current_line.end_ms - current_line.start_ms
        if duration <= 0:
            return 1.0

        elapsed = adjusted_ms - current_line.start_ms
        return max(0.0, min(1.0, elapsed / duration))

    def get_word_index(self, progress_ms: int) -> int:
        if not self.is_synced or not self.lines:
            return -1

        current_idx = self.get_current_index(progress_ms)
        if current_idx < 0:
            return -1

        current_line = self.lines[current_idx]
        if not current_line._word_positions:
            return -1

        adjusted_ms = progress_ms - self.get_effective_offset()

        for i, (start_char, end_char) in enumerate(current_line._word_positions):
            if i + 1 < len(current_line._word_positions):
                next_start = current_line._word_positions[i + 1][0]
                line_duration = (current_line.end_ms or 0) - (current_line.start_ms or 0)
                if line_duration > 0:
                    word_start_ratio = start_char / max(len(current_line.text), 1)
                    word_end_ratio = next_start / max(len(current_line.text), 1)
                    word_start_ms = (current_line.start_ms or 0) + int(word_start_ratio * line_duration)
                    word_end_ms = (current_line.start_ms or 0) + int(word_end_ratio * line_duration)
                    if word_start_ms <= adjusted_ms < word_end_ms:
                        return i

        return len(current_line._word_positions) - 1


class LyricsProvider(ABC):
    """Abstract base class for lyrics providers."""

    @abstractmethod
    def fetch(
        self,
        track_name: str,
        artist_name: str,
        album_name: str | None = None,
        duration_ms: int | None = None,
    ) -> Lyrics | None:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        pass


class LRCLibProvider(LyricsProvider):
    """LRCLib provider - free, no auth required."""

    def __init__(self):
        self.base_url = "https://lrclib.net/api"
        self.client = httpx.Client(
            timeout=10.0,
            headers={"User-Agent": "ethereal-lyrics/0.1.0"},
        )

    @property
    def name(self) -> str:
        return "lrclib"

    @property
    def is_available(self) -> bool:
        return True

    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    def _fuzzy_match(self, a: str, b: str, threshold: float = 0.6) -> bool:
        return SequenceMatcher(None, self._normalize(a), self._normalize(b)).ratio() >= threshold

    def fetch(
        self,
        track_name: str,
        artist_name: str,
        album_name: str | None = None,
        duration_ms: int | None = None,
    ) -> Lyrics | None:
        try:
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
                    return result

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
                            return result

        except httpx.HTTPError:
            return None

        return None

    def _parse_response(
        self,
        data: dict,
        track_name: str,
        artist_name: str,
        album_name: str | None,
    ) -> Lyrics | None:
        synced = data.get("syncedLyrics")
        plain = data.get("plainLyrics")

        lines = []
        is_synced = False

        if synced:
            lines = parse_synced_lyrics(synced)
            is_synced = True
        elif plain:
            lines = parse_plain_lyrics(plain)

        if not lines:
            return None

        return Lyrics(
            track_name=data.get("trackName", track_name),
            artist_name=data.get("artistName", artist_name),
            album_name=data.get("albumName", album_name),
            lines=lines,
            is_synced=is_synced,
            provider=self.name,
        )


class MusixmatchProvider(LyricsProvider):
    """Musixmatch provider - high quality synced lyrics.

    Free tier: 2000 requests/day, but only 30% of lyrics.
    For full lyrics, you need a commercial license.
    """

    BASE_URL = "https://api.musixmatch.com/ws/1.1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.Client(timeout=10.0)

    @property
    def name(self) -> str:
        return "musixmatch"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def _search_track(
        self, track_name: str, artist_name: str
    ) -> str | None:
        """Search for a track and return track_id."""
        try:
            response = self.client.get(
                f"{self.BASE_URL}/track.search",
                params={
                    "q_track": track_name,
                    "q_artist": artist_name,
                    "apikey": self.api_key,
                    "page_size": 5,
                    "s_track_rating": "desc",
                },
            )

            if response.status_code == 200:
                data = response.json()
                tracks = data.get("message", {}).get("body", {}).get("track_list", [])
                for track in tracks:
                    track_info = track.get("track", {})
                    if track_info.get("has_lyrics") == 1:
                        return track_info.get("track_id")
        except httpx.HTTPError:
            pass

        return None

    def _get_lyrics(self, track_id: str) -> dict | None:
        """Get lyrics for a track_id."""
        try:
            response = self.client.get(
                f"{self.BASE_URL}/track.lyrics.get",
                params={
                    "track_id": track_id,
                    "apikey": self.api_key,
                },
            )

            if response.status_code == 200:
                data = response.json()
                lyrics_list = data.get("message", {}).get("body", {}).get("lyrics", [])
                if lyrics_list:
                    return lyrics_list[0] if isinstance(lyrics_list, list) else lyrics_list
        except httpx.HTTPError:
            pass

        return None

    def _get_synced_lyrics(self, track_id: str) -> str | None:
        """Get synced lyrics for a track_id."""
        try:
            response = self.client.get(
                f"{self.BASE_URL}/track.subtitle.get",
                params={
                    "track_id": track_id,
                    "apikey": self.api_key,
                    "subtitle_format": "lrc",
                },
            )

            if response.status_code == 200:
                data = response.json()
                subtitle = data.get("message", {}).get("body", {}).get("subtitle", {})
                return subtitle.get("subtitle_body")
        except httpx.HTTPError:
            pass

        return None

    def fetch(
        self,
        track_name: str,
        artist_name: str,
        album_name: str | None = None,
        duration_ms: int | None = None,
    ) -> Lyrics | None:
        if not self.is_available:
            return None

        # Search for track
        track_id = self._search_track(track_name, artist_name)
        if not track_id:
            return None

        # Try synced lyrics first
        synced = self._get_synced_lyrics(track_id)
        if synced:
            lines = parse_synced_lyrics(synced)
            if lines:
                return Lyrics(
                    track_name=track_name,
                    artist_name=artist_name,
                    album_name=album_name,
                    lines=lines,
                    is_synced=True,
                    provider=self.name,
                )

        # Fallback to plain lyrics
        lyrics_data = self._get_lyrics(track_id)
        if lyrics_data:
            plain = lyrics_data.get("lyrics_body")
            if plain:
                lines = parse_plain_lyrics(plain)
                if lines:
                    return Lyrics(
                        track_name=track_name,
                        artist_name=artist_name,
                        album_name=album_name,
                        lines=lines,
                        is_synced=False,
                        provider=self.name,
                    )

        return None


class MultiProviderLyricsFetcher:
    """Multi-provider lyrics fetcher with fallback."""

    def __init__(
        self,
        musixmatch_api_key: str | None = None,
        genius_access_token: str | None = None,
        static_offset_ms: int = 0,
    ):
        self.providers: list[LyricsProvider] = []
        self._cache: dict[str, Lyrics] = {}
        self._static_offset_ms = static_offset_ms
        self._dynamic_offsets: dict[str, DynamicOffset] = {}

        # Always add LRCLib (free, no auth)
        self.providers.append(LRCLibProvider())

        # Add Musixmatch if API key provided
        if musixmatch_api_key:
            self.providers.append(MusixmatchProvider(musixmatch_api_key))

    def _get_dynamic_offset(self, track_id: str) -> DynamicOffset:
        """Get or create dynamic offset for a track."""
        if track_id not in self._dynamic_offsets:
            self._dynamic_offsets[track_id] = DynamicOffset()
        return self._dynamic_offsets[track_id]

    def update_timing(self, track_id: str, position_ms: int) -> int:
        """Update timing sample and return current dynamic offset."""
        offset = self._get_dynamic_offset(track_id)
        offset.add_sample(position_ms)
        return offset.calculate_offset()

    def reset_timing(self, track_id: str) -> None:
        """Reset timing for a new track."""
        offset = self._get_dynamic_offset(track_id)
        offset.reset(track_id)

    def fetch_lyrics(
        self,
        track_name: str,
        artist_name: str,
        album_name: str | None = None,
        duration_ms: int | None = None,
        track_id: str | None = None,
    ) -> Lyrics | None:
        """Fetch lyrics with fallback across providers."""
        cache_key = f"{artist_name}:{track_name}".lower()
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Attach dynamic offset if track_id provided
            if track_id:
                cached._dynamic_offset = self._get_dynamic_offset(track_id)
            return cached

        for provider in self.providers:
            if not provider.is_available:
                continue

            result = provider.fetch(
                track_name=track_name,
                artist_name=artist_name,
                album_name=album_name,
                duration_ms=duration_ms,
            )

            if result:
                # Set static offset
                result.offset_ms = self._static_offset_ms

                # Attach dynamic offset if track_id provided
                if track_id:
                    result._dynamic_offset = self._get_dynamic_offset(track_id)

                self._cache[cache_key] = result
                return result

        return None

    def get_provider_status(self) -> list[dict]:
        """Get status of all providers."""
        return [
            {"name": p.name, "available": p.is_available}
            for p in self.providers
        ]
