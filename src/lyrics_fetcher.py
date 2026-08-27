"""Multi-provider lyrics fetcher with fallback support.

Providers:
- LRCLib: Free, synced lyrics, no auth required
- Musixmatch: High quality synced lyrics (word-level via desktop API, no key needed)
"""

import httpx
import json
import re
import time
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
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
    _min_samples: int = 2
    _max_samples: int = 10

    _speed_history: list[float] = field(default_factory=list)
    _max_speed_history: int = 8
    _baseline_speed: float = 1.0
    _speed_adjustment: int = 0
    _smoothing_factor: float = 0.3

    def reset(self, track_id: str = "") -> None:
        """Reset calibration for a new track or seek."""
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
            self._speed_adjustment * 0.5 + adjustment * 0.5
        )

        return self._speed_adjustment

    def calculate_offset(self) -> int:
        """Calculate the dynamic offset based on timing drift and speed.

        Returns offset in milliseconds. Negative = lyrics should appear earlier.
        """
        if len(self._samples) < 2:
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
        avg_drift_ms = int(drift_rate * total_time_ms * 0.5)

        # Get speed-based adjustment
        speed_adj = self._calculate_speed_adjustment()

        # Combine drift and speed adjustments
        combined = int(avg_drift_ms * 0.7 + speed_adj * 0.3)

        # Faster convergence: use more aggressive factor early on
        if n < 5:
            factor = 0.7  # 70% new, 30% old (fast convergence)
        else:
            factor = 0.5  # 50/50 (stable)
        self._calibrated_offset = int(
            self._calibrated_offset * (1 - factor) + combined * factor
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

    def _fuzzy_match_track_artist(self, track_a: str, artist_a: str, track_b: str, artist_b: str, threshold: float = 0.8) -> bool:
        """Match both track name and artist name for better accuracy."""
        track_match = SequenceMatcher(None, self._normalize(track_a), self._normalize(track_b)).ratio()
        artist_match = SequenceMatcher(None, self._normalize(artist_a), self._normalize(artist_b)).ratio()
        # Require both to match well, with track being more important
        combined = (track_match * 0.7) + (artist_match * 0.3)
        return combined >= threshold

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
                # Validate the direct get result matches our query
                if self._fuzzy_match_track_artist(
                    data.get("trackName", ""), data.get("artistName", ""),
                    track_name, artist_name
                ):
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
                    if self._fuzzy_match_track_artist(
                        item.get("trackName", ""), item.get("artistName", ""),
                        track_name, artist_name
                    ):
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
    """Musixmatch provider - high quality synced lyrics via desktop API.

    Uses the same unauthenticated desktop API as canticle/sptlrx/musixmatch-freeAPI.
    Automatically obtains and caches tokens. No API key required.
    """

    BASE_URL = "https://apic-desktop.musixmatch.com/ws/1.1/"
    APP_ID = "web-desktop-app-v1.0"
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    def __init__(self):
        self.client = httpx.Client(timeout=15.0, follow_redirects=True)
        self._token: str | None = None
        self._token_at: float = 0.0
        self._token_path = Path.home() / ".cache" / "ethereal-lyrics" / "musixmatch_token.json"
        self._load_cached_token()

    @property
    def name(self) -> str:
        return "musixmatch"

    @property
    def is_available(self) -> bool:
        return True

    def _request(self, endpoint: str, params: dict) -> dict | None:
        """Make an authenticated request to the Musixmatch desktop API."""
        query = {"app_id": self.APP_ID, "format": "json", **params}
        headers = {
            "User-Agent": self.USER_AGENT,
            "Cookie": "x-mxm-token-guid=",
            "x-mxm-user-token": self._token or "",
        }
        try:
            response = self.client.get(
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                params=query,
            )
            if response.status_code == 200:
                text = response.text
                if text.lstrip().startswith("<"):
                    return None
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return None
        except (httpx.HTTPError, json.JSONDecodeError):
            pass
        return None

    def _load_cached_token(self) -> None:
        """Load cached token from disk (valid 6 hours)."""
        try:
            if self._token_path.exists():
                data = json.loads(self._token_path.read_text())
                if data.get("v") and data.get("t", 0) > 0:
                    self._token = data["v"]
                    self._token_at = data["t"]
        except (json.JSONDecodeError, OSError):
            pass

    def _save_token(self, token: str) -> None:
        """Persist token to disk (valid 6 hours)."""
        self._token = token
        self._token_at = time.time()
        try:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
            self._token_path.write_text(json.dumps({"v": token, "t": self._token_at}))
        except OSError:
            pass

    def _get_token(self, force: bool = False) -> str | None:
        """Obtain a user token from the desktop API.

        Tokens are cached for 6 hours. On rate limit (captcha/401),
        retries with exponential backoff.
        """
        self._load_cached_token()
        if not force and self._token and time.time() - self._token_at < 21600:
            return self._token

        for delay in (0, 20, 45, 90):
            if delay:
                time.sleep(delay)
            try:
                ts = str(int(time.time() * 1000))
                data = self._request("token.get", {"t": ts})
                body = (data or {}).get("message", {}).get("body", {})
                if isinstance(body, dict) and "user_token" in body:
                    tok = body["user_token"]
                    if tok and not tok.startswith("UpgradeOnly"):
                        self._save_token(tok)
                        return tok
            except Exception:
                continue

        return self._token

    def _parse_richsync(self, richsync_body: str) -> list[LyricLine]:
        """Parse word-level richsync data into LyricLine objects.

        Richsync format: list of {ts, te, l: [{c, o}], x}
        - ts: line start time (seconds)
        - te: line end time (seconds)
        - l: list of {c: char, o: offset_from_line_start}
        - x: full line text
        """
        try:
            entries = json.loads(richsync_body)
        except (json.JSONDecodeError, TypeError):
            return []

        lines = []
        for entry in entries:
            ts = entry.get("ts", 0)
            te = entry.get("te", ts)
            words = entry.get("l", [])
            line_text = entry.get("x", "").strip()
            if not line_text or not words:
                continue

            start_ms = int(ts * 1000)
            end_ms = int(te * 1000)

            # Build word list and positions from character-level data
            word_list: list[str] = []
            word_positions: list[tuple[int, int]] = []

            current_word = ""
            current_start_char = 0
            for i, item in enumerate(words):
                c = item.get("c", "")
                if c == " ":
                    if current_word:
                        word_list.append(current_word)
                        word_positions.append((current_start_char, current_start_char + len(current_word)))
                        current_word = ""
                    if i + 1 < len(words):
                        current_start_char = i + 1
                else:
                    if not current_word:
                        current_start_char = i
                    current_word += c

            if current_word:
                word_list.append(current_word)
                word_positions.append((current_start_char, current_start_char + len(current_word)))

            line = LyricLine(
                text=line_text,
                start_ms=start_ms,
                end_ms=end_ms,
            )
            if word_list:
                line._words = word_list
                line._word_positions = word_positions
            lines.append(line)

        return lines

    def _parse_subtitles(self, subtitle_body: str) -> list[LyricLine]:
        """Parse line-level subtitle data into LyricLine objects.

        Subtitle format: list of {text, time: {total, minutes, seconds, hundredths}}
        """
        try:
            entries = json.loads(subtitle_body)
        except (json.JSONDecodeError, TypeError):
            return []

        lines = []
        for entry in entries:
            text = entry.get("text", "").strip()
            time_data = entry.get("time", {})
            total = time_data.get("total", 0)
            if not text:
                continue
            lines.append(LyricLine(
                text=text,
                start_ms=int(total * 1000),
            ))

        # Set end_ms from next line start
        for i in range(len(lines)):
            if i + 1 < len(lines):
                lines[i].end_ms = lines[i + 1].start_ms
            else:
                lines[i].end_ms = lines[i].start_ms + 5000

        return lines

    @staticmethod
    def _deep_find(obj, key):
        """Recursively search for a key in nested dicts/lists."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    return v
                r = MusixmatchProvider._deep_find(v, key)
                if r is not None:
                    return r
        elif isinstance(obj, list):
            for v in obj:
                r = MusixmatchProvider._deep_find(v, key)
                if r is not None:
                    return r
        return None

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for fuzzy matching."""
        import unicodedata
        s = unicodedata.normalize("NFKD", text or "")
        s = "".join(c for c in s if not unicodedata.combining(c))
        s = re.sub(r"\(feat\.[^)]*\)|\[[^\]]*\]", " ", s.lower())
        s = re.sub(r"[^a-z0-9]+", " ", s)
        return s.strip()

    def _is_trusted_match(self, track: dict, title: str, artist: str, duration_s: float) -> bool:
        """Verify that the matched track is trustworthy."""
        wt, wa = self._normalize(title), self._normalize(artist)
        gt = self._normalize(track.get("track_name", ""))
        ga = self._normalize(track.get("artist_name", ""))
        tl = track.get("track_length") or 0
        dd = abs(tl - duration_s) if (tl and duration_s) else 9999
        if dd > 15 and dd != 9999:
            return False
        title_ok = bool(gt) and (gt == wt or wt in gt or gt in wt)
        artist_ok = bool(ga) and (ga == wa or wa in ga or ga in wa)
        return (title_ok and artist_ok) or (dd <= 4 and (title_ok or artist_ok))

    def _fetch_with_token(self, track_name: str, artist_name: str, album_name: str | None, duration_ms: int | None, token: str) -> Lyrics | None:
        """Attempt to fetch lyrics with the given token. Returns None on 401 (token refresh needed)."""
        duration_s = duration_ms / 1000 if duration_ms else 0

        # Step 1: macro.subtitles.get — matches track + returns line-level sync
        macro_params = {
            "namespace": "lyrics_richsynched",
            "subtitle_format": "lrc",
            "q_track": track_name,
            "q_artist": artist_name,
            "q_artists": artist_name,
            "q_album": album_name or "",
            "usertoken": token,
        }
        if duration_ms:
            macro_params["q_duration"] = str(int(duration_s))

        macro = self._request("macro.subtitles.get", macro_params)
        if not macro:
            return None

        # Check if macro is a dict (not a string or other type)
        if not isinstance(macro, dict):
            return None

        # Check for token exhaustion
        status = self._deep_find(macro, "status_code")
        if status == 401:
            return None

        # Get matched track
        calls = macro.get("message", {}).get("body", {}).get("macro_calls", {})
        if not isinstance(calls, dict):
            return None
        matcher_calls = calls.get("matcher.track.get", {})
        if not isinstance(matcher_calls, dict):
            return None
        message = matcher_calls.get("message", {})
        if not isinstance(message, dict):
            return None
        body = message.get("body", {})
        if not isinstance(body, dict):
            return None
        matcher_track = body.get("track", {})
        if not matcher_track or not isinstance(matcher_track, dict) or not self._is_trusted_match(matcher_track, track_name, artist_name, duration_s):
            return None

        ctid = matcher_track.get("commontrack_id")
        if not ctid or matcher_track.get("instrumental"):
            return None

        track_name_out = matcher_track.get("track_name", track_name)
        artist_name_out = matcher_track.get("artist_name", artist_name)

        # Step 2: Try richsync (word-level sync) — only if track has it
        if matcher_track.get("has_richsync"):
            time.sleep(1)
            rich = self._request("track.richsync.get", {
                "commontrack_id": ctid,
                "usertoken": token,
                "namespace": "lyrics_richsynched",
                "subtitle_format": "lrc",
            })
            if rich:
                rich_status = self._deep_find(rich, "status_code")
                if rich_status == 401:
                    return None
                rs_body = self._deep_find(rich, "richsync_body")
                if isinstance(rs_body, str) and rs_body:
                    lines = self._parse_richsync(rs_body)
                    if lines:
                        return Lyrics(
                            track_name=track_name_out,
                            artist_name=artist_name_out,
                            album_name=album_name,
                            lines=lines,
                            is_synced=True,
                            provider=self.name,
                        )

        # Step 3: Fallback to line-level subtitles
        sub_body = self._deep_find(macro, "subtitle_body")
        if isinstance(sub_body, str) and "[" in sub_body:
            lines = self._parse_subtitles(sub_body)
            if lines:
                return Lyrics(
                    track_name=track_name_out,
                    artist_name=artist_name_out,
                    album_name=album_name,
                    lines=lines,
                    is_synced=True,
                    provider=self.name,
                )

        # Step 4: Fallback to plain lyrics
        plain = self._deep_find(macro, "lyrics_body")
        if isinstance(plain, str) and plain.strip():
            lines = parse_plain_lyrics(plain)
            if lines:
                return Lyrics(
                    track_name=track_name_out,
                    artist_name=artist_name_out,
                    album_name=album_name,
                    lines=lines,
                    is_synced=False,
                    provider=self.name,
                )

        return None

    def fetch(
        self,
        track_name: str,
        artist_name: str,
        album_name: str | None = None,
        duration_ms: int | None = None,
    ) -> Lyrics | None:
        token = self._get_token()
        if not token:
            return None

        result = self._fetch_with_token(track_name, artist_name, album_name, duration_ms, token)
        if result is not None:
            return result

        # Token may be exhausted — refresh once and retry
        token = self._get_token(force=True)
        if not token:
            return None

        return self._fetch_with_token(track_name, artist_name, album_name, duration_ms, token)


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

        # Always add Musixmatch (desktop API, auto-token, no key needed)
        self.providers.append(MusixmatchProvider())

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
        """Fetch lyrics with fallback across providers.

        Prefers synced lyrics. If a provider returns unsynced lyrics,
        continues to the next provider. Only returns unsynced as last resort.
        """
        cache_key = f"{artist_name}:{track_name}".lower()
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # Attach dynamic offset if track_id provided
            if track_id:
                cached._dynamic_offset = self._get_dynamic_offset(track_id)
            return cached

        unsynced_fallback: Lyrics | None = None

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

                # If synced, use immediately — this is what we want
                if result.is_synced:
                    self._cache[cache_key] = result
                    return result

                # If not synced, save as fallback and keep trying
                if unsynced_fallback is None:
                    unsynced_fallback = result

        # Return synced if found, otherwise unsynced fallback, or None
        if unsynced_fallback:
            self._cache[cache_key] = unsynced_fallback
            return unsynced_fallback

        return None

    def get_provider_status(self) -> list[dict]:
        """Get status of all providers."""
        return [
            {"name": p.name, "available": p.is_available}
            for p in self.providers
        ]
