"""Spotify client for fetching currently playing track."""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    """Represents a currently playing track."""

    name: str
    artists: str
    album: str
    duration_ms: int
    progress_ms: int
    is_playing: bool
    album_art_url: Optional[str] = None
    spotify_url: Optional[str] = None
    track_id: Optional[str] = None


class SpotifyClient:
    """Handles Spotify API interactions."""

    SCOPE = "user-read-currently-playing user-read-playback-position"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize Spotify client with OAuth authentication."""
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=self.SCOPE,
                open_browser=True,
                cache_path=".spotify_cache",
            )
        )

    def get_current_track(self) -> Optional[Track]:
        """Get the currently playing track from Spotify.

        Returns:
            Track object or None if nothing is playing.
        """
        try:
            current = self.sp.currently_playing()
        except spotipy.SpotifyException:
            return None

        if not current or current.get("item") is None:
            return None

        item = current["item"]
        artists = ", ".join(
            artist["name"] for artist in item.get("artists", [])
        )

        album = item.get("album", {}).get("name", "Unknown Album")
        duration_ms = item.get("duration_ms", 0)
        progress_ms = current.get("progress_ms", 0)
        is_playing = current.get("is_playing", False)
        track_id = item.get("id")

        album_art_url = None
        if item.get("album", {}).get("images"):
            album_art_url = item["album"]["images"][0]["url"]

        external_urls = item.get("external_urls", {})
        spotify_url = external_urls.get("spotify")

        return Track(
            name=item["name"],
            artists=artists,
            album=album,
            duration_ms=duration_ms,
            progress_ms=progress_ms,
            is_playing=is_playing,
            album_art_url=album_art_url,
            spotify_url=spotify_url,
            track_id=track_id,
        )

    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        try:
            self.sp.current_user()
            return True
        except Exception:
            return False
