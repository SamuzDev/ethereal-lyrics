"""Configuration management for lyrica."""

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    spotify_client_id: str = Field(default="", env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(default="", env="SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str = Field(
        default="http://localhost:8888/callback", env="SPOTIFY_REDIRECT_URI"
    )

    # LRCLib API (free, no auth needed)
    lrclib_base_url: str = "https://lrclib.net/api"

    # Terminal UI settings
    lyric_color: str = Field(default="white", env="LYRIC_COLOR")
    highlight_color: str = Field(default="bold white", env="HIGHLIGHT_COLOR")
    dim_color: str = Field(default="dim white", env="DIM_COLOR")

    # Sync tolerance in milliseconds
    sync_tolerance_ms: int = 200

    # Lyric timing offset in milliseconds (positive = lyrics appear later)
    lyric_offset_ms: int = Field(default=0, env="LYRIC_OFFSET_MS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
