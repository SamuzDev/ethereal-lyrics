"""Ethereal Lyrics - Display Spotify lyrics in your terminal."""

import sys
import os
import time
import signal
import atexit
import tty
import termios
import threading
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
            static_offset_ms=self.settings.lyric_offset_ms,
        )
        self.ui = TerminalUI(
            offset_ms=self.settings.lyric_offset_ms,
            color=self.settings.lyric_color,
            word_count=self.settings.lyric_words,
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
        self._current_track_name: str = ""
        self._current_lyrics: Lyrics | None = None
        self._last_progress_ms: int = 0
        self._running = True
        self._term_fd = sys.stdin.fileno()
        self._term_settings = None
        self._is_tty = os.isatty(self._term_fd)
        self._lyrics_thread: threading.Thread | None = None
        self._lyrics_lock = threading.Lock()
        self._pending_fetch: tuple | None = None
        self._fetching_lyrics: bool = False

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self._restore_terminal)

    def _setup_terminal(self) -> None:
        """Set terminal to cbreak mode for single-keystroke reading."""
        if not self._is_tty:
            return
        try:
            self._term_settings = termios.tcgetattr(self._term_fd)
            tty.setcbreak(self._term_fd)
        except (termios.error, OSError):
            self._is_tty = False
            self._term_settings = None

    def _restore_terminal(self) -> None:
        """Restore terminal to original settings."""
        if self._is_tty and self._term_settings is not None:
            try:
                termios.tcsetattr(self._term_fd, termios.TCSADRAIN, self._term_settings)
            except (OSError, IOError):
                pass

    def _signal_handler(self, signum: int, frame) -> None:
        self._running = False
        self.ui.stop()
        self._restore_terminal()

    def _check_keypress(self) -> str | None:
        """Check for keypress without blocking."""
        if self._is_tty:
            # In cbreak mode - read from stdin directly
            try:
                import select
                r, _, _ = select.select([self._term_fd], [], [], 0)
                if r:
                    data = os.read(self._term_fd, 1)
                    return data.decode('utf-8', errors='ignore') if data else None
            except (OSError, IOError, ValueError):
                pass
            return None

        # Fallback for non-TTY: try stdin then /dev/tty
        try:
            import select
            r, _, _ = select.select([self._term_fd], [], [], 0)
            if r:
                data = os.read(self._term_fd, 1)
                return data.decode('utf-8', errors='ignore') if data else None
        except (OSError, IOError, ValueError):
            pass

        # Fallback: read directly from /dev/tty
        try:
            tty_fd = os.open("/dev/tty", os.O_RDONLY)
            try:
                import fcntl
                flags = fcntl.fcntl(tty_fd, fcntl.F_GETFL)
                fcntl.fcntl(tty_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                r, _, _ = select.select([tty_fd], [], [], 0)
                if r:
                    data = os.read(tty_fd, 1)
                    return data.decode('utf-8', errors='ignore') if data else None
            finally:
                os.close(tty_fd)
        except (OSError, IOError, ValueError):
            pass

        return None

    def _fetch_lyrics_for_track(self, name: str, artist: str, album: str, duration_ms: int, track_id: str | None = None) -> Lyrics | None:
        artist_name = artist.split(",")[0].strip()
        return self.lyrics_fetcher.fetch_lyrics(
            track_name=name,
            artist_name=artist_name,
            album_name=album,
            duration_ms=duration_ms,
            track_id=track_id,
        )

    def _fetch_lyrics_async(self, name: str, artist: str, album: str, duration_ms: int, track_id: str, track_changed: bool) -> None:
        """Start background lyrics fetch."""
        # Cancel any existing fetch
        if self._lyrics_thread and self._lyrics_thread.is_alive():
            return  # Let the existing one finish

        self._pending_fetch = None  # Discard stale results
        self._fetching_lyrics = True

        def fetch_and_store():
            try:
                lyrics = self._fetch_lyrics_for_track(name, artist, album, duration_ms, track_id)
            except Exception:
                lyrics = None
            with self._lyrics_lock:
                self._pending_fetch = (track_id, name, lyrics, track_changed)
                self._fetching_lyrics = False
        
        self._lyrics_thread = threading.Thread(target=fetch_and_store, daemon=True)
        self._lyrics_thread.start()

    def _check_pending_lyrics(self) -> None:
        """Check if background lyrics fetch completed and apply results."""
        with self._lyrics_lock:
            if self._pending_fetch is not None:
                track_id, name, lyrics, track_changed = self._pending_fetch
                self._current_track_id = track_id
                self._current_track_name = name
                self._current_lyrics = lyrics
                self._pending_fetch = None

    def run(self):
        self._setup_terminal()
        self.ui.console.clear()

        while self._running:
            try:
                # Check for quit key
                key = self._check_keypress()
                if key and key.lower() in ('q', '\x03'):  # q or Ctrl+C
                    self._running = False
                    break

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
                    self.ui.render(None, None, False)
                    time.sleep(0.3)
                    continue

                # Use name+artist as fallback track_id if D-Bus doesn't provide one
                if not track_id:
                    track_id = f"{artist}:{name}"

                render_track = RenderTrack(
                    name=name,
                    artists=artist,
                    album=album,
                    duration_ms=duration_ms,
                    progress_ms=progress_ms,
                    is_playing=is_playing,
                    track_id=track_id,
                )

                # Detect track change by track_id OR by name change
                track_changed = (
                    track_id != self._current_track_id
                    or name != self._current_track_name
                )

                if track_changed:
                    self._current_track_id = track_id
                    self._current_track_name = name
                    self._last_progress_ms = progress_ms
                    self.ui._prev_lyric_idx = -1
                    self.ui._word_index = 0
                    self.lyrics_fetcher.reset_timing(track_id)
                    if self._use_local and self._local_client:
                        self._local_client.reset_interpolation()
                    self._current_lyrics = None
                    self._fetch_lyrics_async(name, artist, album, duration_ms, track_id, track_changed)
                elif track_id and abs(progress_ms - self._last_progress_ms) > 2000:
                    # Seek detected — reset dynamic offset
                    self.lyrics_fetcher.reset_timing(track_id)
                    self._last_progress_ms = progress_ms
                else:
                    self._last_progress_ms = progress_ms
 
                if track_id:
                    self.lyrics_fetcher.update_timing(track_id, progress_ms)
 
                # Check for completed background lyrics fetch
                self._check_pending_lyrics()
 
                # Only show loading when we have no lyrics yet
                show_fetching = self._fetching_lyrics and self._current_lyrics is None
                self.ui.render(render_track, self._current_lyrics, show_fetching)
                time.sleep(0.05)

            except KeyboardInterrupt:
                self._running = False
                break
            except Exception as e:
                self.ui.stop()
                self._restore_terminal()
                self.ui.print_error(str(e))
                time.sleep(2)

        self.ui.stop()
        self._restore_terminal()


def show_lyrics_debug():
    """Show raw lyrics data from API for the currently playing track."""
    load_dotenv()
    settings = get_settings()

    fetcher = MultiProviderLyricsFetcher(
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

    if not lyrics or not hasattr(lyrics, 'lines'):
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

    def cleanup():
        app.ui.stop()

    atexit.register(cleanup)
    app.run()


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    # Handle -h/--help
    if "-h" in args or "--help" in args:
        print("""ethereal-lyrics - synced lyrics in your terminal

Usage:
  ethereal-lyrics              Run the lyrics display
  ethereal-lyrics [OPTIONS]

Options:
  -l, --lyrics        Show raw lyrics data for current track
  -u, --update        Update to latest version
  -c, --check-update  Check for available updates
  -v, --version       Show current version
  -C, --color COLOR   Override lyric color (e.g. cyan, magenta, 196)
  -W, --words N       Words per screen (0=auto, default: 0)
  -h, --help          Show this help message

Environment Variables:
  LYRIC_OFFSET_MS     Lyric timing offset in ms (default: 0)
  LYRIC_COLOR         Lyric text color (default: bold white)
  SPOTIFY_CLIENT_ID   Spotify API client ID (optional)
  SPOTIFY_CLIENT_SECRET Spotify API client secret (optional)

Examples:
  ethereal-lyrics
  ethereal-lyrics --lyrics
  ethereal-lyrics --update
  ethereal-lyrics --color cyan
  ethereal-lyrics -C 196
  ethereal-lyrics -C 'bold magenta'
  LYRIC_COLOR=magenta ethereal-lyrics
""")
        sys.exit(0)

    # Handle -v/--version
    if "-v" in args or "--version" in args:
        from .updater import get_current_version
        print(f"ethereal-lyrics v{get_current_version()}")
        sys.exit(0)

    # Handle -u/--update
    if "-u" in args or "--update" in args:
        try:
            from .updater import check_for_updates
            check_for_updates(silent=False)
        except Exception as e:
            print(f"Update failed: {e}", file=sys.stderr)
        sys.exit(0)

    # Handle -c/--check-update
    if "-c" in args or "--check-update" in args:
        try:
            from .updater import get_current_version, get_latest_version, _parse_version
            current = get_current_version()
            latest = get_latest_version()
            print(f"Current version: v{current}")
            if latest:
                if _parse_version(current) < _parse_version(latest):
                    print(f"Latest version:  v{latest}")
                    print(f"\nRun: ethereal-lyrics --update")
                    sys.exit(1)
                else:
                    print(f"Latest version:  v{latest} (up to date)")
            else:
                print("Could not check for updates")
        except Exception as e:
            print(f"Check failed: {e}", file=sys.stderr)
        sys.exit(0)

    # Handle -l/--lyrics
    if "-l" in args or "--lyrics" in args:
        try:
            from .main import show_lyrics_debug
            show_lyrics_debug()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(0)

    # Handle -C/--color
    for i, arg in enumerate(args):
        if arg in ("-C", "--color"):
            if i + 1 < len(args):
                color_val = args[i + 1]
                if color_val.isdigit() and 1 <= int(color_val) <= 256:
                    os.environ["LYRIC_COLOR"] = f"color({color_val})"
                else:
                    os.environ["LYRIC_COLOR"] = color_val
            break

    # Handle -W/--words
    for i, arg in enumerate(args):
        if arg in ("-W", "--words"):
            if i + 1 < len(args) and args[i + 1].isdigit():
                word_count = max(1, int(args[i + 1]))
                os.environ["LYRIC_WORDS"] = str(word_count)
            break

    # Check for unknown arguments
    valid_flags = {"-l", "--lyrics", "-u", "--update", "-c", "--check-update",
                   "-v", "--version", "-C", "--color", "-W", "--words", "-h", "--help"}
    skip_args = set()
    for i, arg in enumerate(args):
        if arg in ("-C", "--color", "-W", "--words") and i + 1 < len(args):
            skip_args.add(args[i + 1])

    for arg in args:
        if arg.startswith("-") and arg not in valid_flags and arg not in skip_args:
            print(f"\033[0;31m\u2717\033[0m Unknown option: \033[1;33m{arg}\033[0m")
            print("  Run 'ethereal-lyrics -h' for usage information.")
            sys.exit(1)

    main()
