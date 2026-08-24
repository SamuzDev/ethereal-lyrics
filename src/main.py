"""Ethereal Lyrics - Display Spotify lyrics in your terminal."""

import sys
import time
import signal
from dataclasses import dataclass
from pathlib import Path
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
        """Initialize the application."""
        # Load environment variables
        load_dotenv()

        # Load settings
        self.settings = get_settings()

        # Initialize lyrics fetcher and UI
        self.lyrics_fetcher = MultiProviderLyricsFetcher(
            musixmatch_api_key=self.settings.musixmatch_api_key,
            genius_access_token=self.settings.genius_access_token,
            static_offset_ms=self.settings.lyric_offset_ms,
        )
        self.ui = TerminalUI(offset_ms=self.settings.lyric_offset_ms)

        # Try local detection first (no credentials needed)
        self._local_client = LocalSpotifyClient()
        self._spotify_client: SpotifyClient | None = None
        self._use_local = True

        # Fallback to API client if credentials are provided
        if self.settings.spotify_client_id and self.settings.spotify_client_secret:
            try:
                self._spotify_client = SpotifyClient(
                    client_id=self.settings.spotify_client_id,
                    client_secret=self.settings.spotify_client_secret,
                    redirect_uri=self.settings.spotify_redirect_uri,
                )
                # Test if local detection works
                if self._local_client.is_spotify_running():
                    self.ui.print_info("Using local D-Bus detection (no login needed)")
                    self._use_local = True
                else:
                    self.ui.print_info("Local detection unavailable, using Spotify API")
                    self._use_local = False
            except Exception:
                self._use_local = True
        else:
            self.ui.print_info("No Spotify credentials — using local D-Bus detection")

        # State
        self._current_track_id: str | None = None
        self._current_lyrics: Lyrics | None = None
        self._running = True

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle interrupt signals."""
        self._running = False
        self.ui.console.clear()

    def _fetch_lyrics_for_track(self, name: str, artist: str, album: str, duration_ms: int, track_id: str | None = None) -> Lyrics | None:
        """Fetch lyrics for the given track."""
        # Split artists (Spotify returns them comma-separated)
        artist_name = artist.split(",")[0].strip()

        return self.lyrics_fetcher.fetch_lyrics(
            track_name=name,
            artist_name=artist_name,
            album_name=album,
            duration_ms=duration_ms,
            track_id=track_id,
        )

    def _get_local_track(self) -> LocalTrack | None:
        """Get track from local D-Bus detection."""
        return self._local_client.get_current_track()

    def _get_api_track(self) -> Track | None:
        """Get track from Spotify API."""
        if self._spotify_client is None:
            return None
        return self._spotify_client.get_current_track()

    def run(self):
        """Main application loop."""
        # Clear screen and show initial state
        self.ui.console.clear()
        self.ui.print_info("Detecting Spotify...")
        time.sleep(1)

        # Main loop
        while self._running:
            try:
                track = None
                track_id = None
                name = artist = album = ""
                duration_ms = 0
                progress_ms = 0
                is_playing = False

                if self._use_local:
                    # Local D-Bus detection
                    local_track = self._get_local_track()
                    if local_track is not None:
                        name = local_track.name
                        artist = local_track.artist
                        album = local_track.album
                        duration_ms = local_track.duration_ms
                        progress_ms = local_track.position_ms
                        is_playing = local_track.is_playing
                        track_id = local_track.track_id or f"{artist}:{name}"
                else:
                    # Spotify API detection
                    api_track = self._get_api_track()
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

                # Create a unified track object for the UI
                render_track = RenderTrack(
                    name=name,
                    artists=artist,
                    album=album,
                    duration_ms=duration_ms,
                    progress_ms=progress_ms,
                    is_playing=is_playing,
                    track_id=track_id,
                )

                # Check if track changed
                if track_id != self._current_track_id:
                    self._current_track_id = track_id
                    self.lyrics_fetcher.reset_timing(track_id)
                    self._current_lyrics = self._fetch_lyrics_for_track(
                        name, artist, album, duration_ms, track_id
                    )

                # Update dynamic offset with current position
                if track_id:
                    self.lyrics_fetcher.update_timing(track_id, progress_ms)

                # Render
                self.ui.render(render_track, self._current_lyrics)

                # Wait before next update
                time.sleep(0.5)

            except KeyboardInterrupt:
                self._running = False
                break
            except Exception as e:
                self.ui.print_error(str(e))
                time.sleep(2)

        # Cleanup
        self.ui.stop()
        self.ui.console.clear()


def main():
    """Entry point for the application."""
    app = EtherealLyrics()
    app.run()


if __name__ == "__main__":
    main()
