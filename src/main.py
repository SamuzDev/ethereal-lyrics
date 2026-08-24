"""Ethereal Lyrics - Display Spotify lyrics in your terminal."""

import sys
import time
import signal
from dataclasses import dataclass
from dotenv import load_dotenv

from .config import get_settings
from .spotify_client import SpotifyClient, Track
from .local_spotify import LocalSpotifyClient, LocalTrack
from .lyrics_fetcher import MultiProviderLyricsFetcher, Lyrics
from .terminal_ui import TerminalUI


@dataclass
class RenderTrack:
    """Unified track representation for the UI."""

    name: str
    artists: str
    album: str
    duration_ms: int
    progress_ms: int
    is_playing: bool
    track_id: str | None = None


class EtherealLyrics:
    """Main application class."""

    def __init__(self):
        load_dotenv()
        self.settings = get_settings()

        self.lyrics_fetcher = MultiProviderLyricsFetcher(
            musixmatch_api_key=self.settings.musixmatch_api_key,
            static_offset_ms=self.settings.lyric_offset_ms,
        )
        self.ui = TerminalUI(
            offset_ms=self.settings.lyric_offset_ms,
            color=self.settings.lyric_color,
        )

        self._local_client = LocalSpotifyClient()
        self._spotify_client: SpotifyClient | None = None
        self._use_local = True

        if self.settings.spotify_client_id and self.settings.spotify_client_secret:
            try:
                self._spotify_client = SpotifyClient(
                    client_id=self.settings.spotify_client_id,
                    client_secret=self.settings.spotify_client_secret,
                    redirect_uri=self.settings.spotify_redirect_uri,
                )
                if self._local_client.is_spotify_running():
                    self._use_local = True
                else:
                    self._use_local = False
            except Exception:
                self._use_local = True
        else:
            self._use_local = True

        self._current_track_id: str | None = None
        self._current_lyrics: Lyrics | None = None
        self._last_progress_ms: int = 0
        self._running = True

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        self._running = False
        self.ui.console.clear()

    def _fetch_lyrics_for_track(self, name: str, artist: str, album: str, duration_ms: int, track_id: str | None = None) -> Lyrics | None:
        artist_name = artist.split(",")[0].strip()
        return self.lyrics_fetcher.fetch_lyrics(
            track_name=name,
            artist_name=artist_name,
            album_name=album,
            duration_ms=duration_ms,
            track_id=track_id,
        )

    def run(self):
        self.ui.console.clear()
        if self._spotify_client and not self._use_local:
            self.ui.print_info("Using Spotify API")
        else:
            self.ui.print_info("No Spotify credentials — using local D-Bus detection")
        self.ui.print_info("Detecting Spotify...")
        time.sleep(1)

        while self._running:
            try:
                track = None
                track_id = None
                name = artist = album = ""
                duration_ms = 0
                progress_ms = 0
                is_playing = False

                if self._use_local:
                    local_track = self._local_client.get_current_track()
                    if local_track is not None:
                        name = local_track.name
                        artist = local_track.artist
                        album = local_track.album
                        duration_ms = local_track.duration_ms
                        progress_ms = local_track.position_ms
                        is_playing = local_track.is_playing
                        track_id = local_track.track_id or f"{artist}:{name}"
                else:
                    api_track = self._spotify_client.get_current_track() if self._spotify_client else None
                    if api_track is not None:
                        name = api_track.name
                        artist = api_track.artists
                        album = api_track.album
                        duration_ms = api_track.duration_ms
                        progress_ms = api_track.progress_ms
                        is_playing = api_track.is_playing
                        track_id = api_track.track_id

                if not name:
                    self.ui.render(None, None)
                    time.sleep(3)
                    continue

                render_track = RenderTrack(
                    name=name,
                    artists=artist,
                    album=album,
                    duration_ms=duration_ms,
                    progress_ms=progress_ms,
                    is_playing=is_playing,
                    track_id=track_id,
                )

                if track_id != self._current_track_id:
                    self._current_track_id = track_id
                    self._last_progress_ms = progress_ms
                    self.lyrics_fetcher.reset_timing(track_id)
                    self._current_lyrics = self._fetch_lyrics_for_track(
                        name, artist, album, duration_ms, track_id
                    )
                elif track_id and abs(progress_ms - self._last_progress_ms) > 2000:
                    # Seek detected — reset dynamic offset
                    self.lyrics_fetcher.reset_timing(track_id)
                    self._last_progress_ms = progress_ms
                else:
                    self._last_progress_ms = progress_ms

                if track_id:
                    self.lyrics_fetcher.update_timing(track_id, progress_ms)

                self.ui.render(render_track, self._current_lyrics)
                time.sleep(0.05)

            except KeyboardInterrupt:
                self._running = False
                break
            except Exception as e:
                self.ui.print_error(str(e))
                time.sleep(2)

        self.ui.stop()
        self.ui.console.clear()


def show_lyrics_debug():
    """Show raw lyrics data from API for the currently playing track."""
    load_dotenv()
    settings = get_settings()

    fetcher = MultiProviderLyricsFetcher(
        musixmatch_api_key=settings.musixmatch_api_key,
        static_offset_ms=settings.lyric_offset_ms,
    )
    local_client = LocalSpotifyClient()

    track = local_client.get_current_track()
    if not track:
        print("\u2717 No track playing. Start Spotify and try again.")
        return

    artist_name = track.artist.split(",")[0].strip()
    print(f"\n  Track:   {track.name}")
    print(f"  Artist:  {track.artist}")
    print(f"  Album:   {track.album}")
    print(f"  Position: {track.position_ms}ms / {track.duration_ms}ms")
    print()

    lyrics = fetcher.fetch_lyrics(
        track_name=track.name,
        artist_name=artist_name,
        album_name=track.album,
        duration_ms=track.duration_ms,
        track_id=track.track_id,
    )

    if not lyrics:
        print("  \u2717 No lyrics found")
        return

    dynamic_offset = 0
    if lyrics._dynamic_offset:
        dynamic_offset = lyrics._dynamic_offset.calculate_offset()

    print(f"  Provider:        {lyrics.provider}")
    print(f"  Synced:          {'yes' if lyrics.is_synced else 'no'}")
    print(f"  Lines:           {len(lyrics.lines)}")
    print(f"  Static offset:   {lyrics.offset_ms}ms")
    print(f"  Dynamic offset:  {dynamic_offset}ms")
    print(f"  Effective offset:{lyrics.get_effective_offset()}ms")
    print()

    for line in lyrics.lines:
        if line.start_ms is not None:
            mins = line.start_ms // 60000
            secs = (line.start_ms // 1000) % 60
            ms = (line.start_ms % 1000) // 10
            ts = f"[{mins:02d}:{secs:02d}.{ms:02d}]"
        else:
            ts = "        "
        print(f"  {ts} {line.text}")

    print()


def main():
    app = EtherealLyrics()
    app.run()


if __name__ == "__main__":
    main()
