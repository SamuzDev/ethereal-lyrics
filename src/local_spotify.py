"""Local Spotify client using D-Bus MPRIS (no credentials needed)."""

import time
from dataclasses import dataclass


@dataclass
class LocalTrack:
    """Represents a track detected via local D-Bus."""

    name: str
    artist: str
    album: str
    duration_ms: int
    position_ms: int
    is_playing: bool
    track_id: str | None = None


class LocalSpotifyClient:
    """Detects Spotify playback via D-Bus MPRIS on Linux.

    This method reads playback state directly from the Spotify desktop
    client through the D-Bus session bus, requiring no OAuth credentials.
    """

    BUS_NAME = "org.mpris.MediaPlayer2.spotify"
    OBJECT_PATH = "/org/mpris/MediaPlayer2"
    INTERFACE = "org.mpris.MediaPlayer2.Player"
    PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"

    def __init__(self):
        self._bus = None
        self._player = None
        self._properties = None
        self._connected = False
        self._is_playing = False
        self._last_position: int = 0
        self._last_read_time: float = 0.0

    def _ensure_connected(self) -> bool:
        if self._connected:
            return True

        try:
            import dbus

            self._bus = dbus.SessionBus()
            proxy = self._bus.get_object(self.BUS_NAME, self.OBJECT_PATH)
            self._player = dbus.Interface(proxy, self.INTERFACE)
            self._properties = dbus.Interface(proxy, self.PROPERTIES_IFACE)
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def _get_metadata(self) -> dict | None:
        if not self._ensure_connected():
            return None

        try:
            metadata = self._properties.Get(self.INTERFACE, "Metadata")
            return dict(metadata)
        except Exception:
            self._connected = False
            return None

    def _get_playback_status(self) -> str | None:
        if not self._ensure_connected():
            return None

        try:
            status = self._properties.Get(self.INTERFACE, "PlaybackStatus")
            return str(status)
        except Exception:
            self._connected = False
            return None

    def _get_position(self) -> int:
        """Get current position in milliseconds from D-Bus."""
        if not self._ensure_connected():
            return 0

        try:
            position = self._properties.Get(self.INTERFACE, "Position")
            return int(position) // 1000
        except Exception:
            return 0

    def get_interpolated_position(self) -> int:
        """Get position interpolated between D-Bus reads.

        When playing, estimates the current position based on the last
        D-Bus read plus elapsed wall-clock time, eliminating the
        systematic lag from polling delay.
        """
        status = self._get_playback_status()
        self._is_playing = status == "Playing"

        position = self._get_position()
        now = time.monotonic()

        if self._is_playing and self._last_read_time > 0:
            elapsed_ms = int((now - self._last_read_time) * 1000)
            position = self._last_position + elapsed_ms

        self._last_position = position
        self._last_read_time = now
        return position

    def get_current_track(self) -> LocalTrack | None:
        """Get the currently playing track from local Spotify."""
        metadata = self._get_metadata()
        status = self._get_playback_status()

        if metadata is None or status is None:
            return None

        title = str(metadata.get("xesam:title", ""))
        if not title:
            return None

        artist_raw = metadata.get("xesam:artist", "")
        if isinstance(artist_raw, (list, tuple)):
            artist = ", ".join(str(a) for a in artist_raw)
        else:
            artist = str(artist_raw)

        album = str(metadata.get("xesam:album", ""))
        duration_us = int(metadata.get("mpris:length", 0))
        duration_ms = duration_us // 1000

        track_id = None
        url = str(metadata.get("mpris:trackid", ""))
        if url.startswith("spotify:track:"):
            track_id = url.split(":")[-1]

        position_ms = self.get_interpolated_position()
        is_playing = status == "Playing"

        return LocalTrack(
            name=title,
            artist=artist,
            album=album,
            duration_ms=duration_ms,
            position_ms=position_ms,
            is_playing=is_playing,
            track_id=track_id,
        )

    def is_spotify_running(self) -> bool:
        return self._ensure_connected()
