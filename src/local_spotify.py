"""Local Spotify client using D-Bus MPRIS (no credentials needed)."""

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
        """Initialize the local Spotify client."""
        self._bus = None
        self._player = None
        self._properties = None
        self._connected = False

    def _ensure_connected(self) -> bool:
        """Try to connect to D-Bus and get Spotify player interface."""
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
        """Get track metadata from D-Bus."""
        if not self._ensure_connected():
            return None

        try:
            metadata = self._properties.Get(self.INTERFACE, "Metadata")
            return dict(metadata)
        except Exception:
            self._connected = False
            return None

    def _get_playback_status(self) -> str | None:
        """Get playback status from D-Bus."""
        if not self._ensure_connected():
            return None

        try:
            status = self._properties.Get(self.INTERFACE, "PlaybackStatus")
            return str(status)
        except Exception:
            self._connected = False
            return None

    def _get_position(self) -> int:
        """Get current position in milliseconds."""
        if not self._ensure_connected():
            return 0

        try:
            position = self._properties.Get(self.INTERFACE, "Position")
            return int(position) // 1000  # microseconds to milliseconds
        except Exception:
            return 0

    def get_current_track(self) -> LocalTrack | None:
        """Get the currently playing track from local Spotify.

        Returns:
            LocalTrack object or None if nothing is playing or
            Spotify is not running.
        """
        metadata = self._get_metadata()
        status = self._get_playback_status()

        if metadata is None or status is None:
            return None

        # Extract track info from metadata
        title = str(metadata.get("xesam:title", ""))
        if not title:
            return None

        # Artist can be a list or string
        artist_raw = metadata.get("xesam:artist", "")
        if isinstance(artist_raw, (list, tuple)):
            artist = ", ".join(str(a) for a in artist_raw)
        else:
            artist = str(artist_raw)

        album = str(metadata.get("xesam:album", ""))
        duration_us = int(metadata.get("mpris:length", 0))
        duration_ms = duration_us // 1000

        # Extract track ID from URL if available
        track_id = None
        url = str(metadata.get("mpris:trackid", ""))
        if url.startswith("spotify:track:"):
            track_id = url.split(":")[-1]

        position_ms = self._get_position()
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
        """Check if Spotify is registered on D-Bus."""
        return self._ensure_connected()
