"""Configuration management for ethereal lyrics."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    spotify_client_id: str = Field(default="", env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(default="", env="SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str = Field(
        default="http://localhost:8888/callback", env="SPOTIFY_REDIRECT_URI"
    )

    musixmatch_api_key: str = Field(default="", env="MUSIXMATCH_API_KEY")
    genius_access_token: str = Field(default="", env="GENIUS_ACCESS_TOKEN")

    lyric_offset_ms: int = Field(default=0, env="LYRIC_OFFSET_MS")

    lyric_color: str = Field(default="bold white", env="LYRIC_COLOR")

    lyric_words: int = Field(default=1, env="LYRIC_WORDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
