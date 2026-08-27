# ethereal lyrics

**Synced Spotify lyrics in your terminal with block character art.**

[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://linux.org/)

---

## Preview

[https://private-user-images.githubusercontent.com/108047432/640066507-b70bee4d-2869-4f20-bd54-cc32f3370c8b.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3ODc1MzYzOTcsIm5iZiI6MTc4NzUzNjA5NywicGF0aCI6Ii8xMDgwNDc0MzIvNjQwMDY2NTA3LWI3MGJlZTRkLTI4NjktNGYyMC1iZDU0LWNjMzJmMzM3MGM4Yi5tcDQ_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjYwODI0JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI2MDgyNFQwMTQ4MTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT1iMTdmNmY3MDliYWZjYmEyYTIwZDRhMmY1MGYxYzM5MThhYjc2Yzk0ZmM4NmI5ZDE0ZWY1MDE1ZGMyNjg0MGUwJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZyZXNwb25zZS1jb250ZW50LXR5cGU9dmlkZW8lMkZtcDQifQ.ySRP_2rQaYF8w9Hl90aitBtrnUzj63X2YyQZmW_WrA4](https://github.com/user-attachments/assets/e140bee9-0d43-4eb0-965a-044b2ec0378d)

---

## Features

- **Real-time synced lyrics** — words highlight as the song plays
- **Block character art** — custom 7x6 pixel font rendered with unicode block elements
- **Smart synchronization** — dynamic offset detection adapts to each song
- **Seek detection** — automatically re-syncs when you skip or rewind
- **LRCLib integration** — free synced lyrics, no API key or login required
- **Spotify detection** — auto-detects currently playing track via D-Bus (no Spotify API needed)
- **Lightweight** — single binary, no dependencies

---

## Install

### One-liner (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/SamuzDev/ethereal-lyrics/main/install.sh | bash
```

This downloads the precompiled binary to `~/.local/bin/ethereal-lyrics`.

### Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/SamuzDev/ethereal-lyrics/main/install.sh | bash -s -- uninstall
```

### From source

Requires Python 3.10+.

```bash
git clone https://github.com/SamuzDev/ethereal-lyrics.git
cd ethereal-lyrics
pip install .
```

---

## Usage

```bash
ethereal-lyrics              # Run the lyrics display
ethereal-lyrics --lyrics     # Show raw lyrics data for current track
ethereal-lyrics --update     # Update to latest version
ethereal-lyrics --version    # Show current version
```

### Options

| Flag | Description |
|------|-------------|
| `-l`, `--lyrics` | Show raw lyrics data (provider, sync status, timestamps) |
| `-u`, `--update` | Update to latest version |
| `-c`, `--check-update` | Check for available updates |
| `-v`, `--version` | Show current version |
| `-C`, `--color COLOR` | Override lyric color (e.g. `cyan`, `magenta`, `196`) |
| `-W`, `--words N` | Words per screen (`0` = auto, default) |
| `-h`, `--help` | Show help message |

### Controls

| Key | Action |
|-----|--------|
| `q` | Quit |

---

## Configuration

Optional `.env` file in the project root:

```env
# Lyric timing offset (milliseconds)
# Positive = lyrics appear later, negative = earlier
LYRIC_OFFSET_MS=0

# Lyric text color (default: bold white)
LYRIC_COLOR=bold white

# Spotify API (only needed for web player detection)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

> **Note:** The app works without any configuration using local D-Bus detection.

---

## How It Works

1. **Detection** — detects Spotify playback via D-Bus (no login needed)
2. **Lyrics** — fetches synced lyrics from [LRCLib](https://lrclib.net/) (free, no API key)
3. **Display** — renders lyrics as block character art with real-time word highlighting
4. **Sync** — dynamic offset detection adapts to each song's timing

---

## Dependencies

**Binary (recommended):** none — everything is included.

**From source:**

- Python 3.10+
- [Rich](https://github.com/Textualize/rich) — terminal formatting
- [httpx](https://www.python-httpx.org/) — HTTP client
- [Spotipy](https:// spotipy.readthedocs.io/) — Spotify API (optional)
- [dbus-python](https://github.com/altdesktop/python-dbus) — D-Bus detection (Linux)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [LRCLib](https://lrclib.net/) — free synced lyrics API
- [Rich](https://github.com/Textualize/rich) — beautiful terminal formatting
- [Tokyo Night](https://github.com/enkia/tokyo-night-vscode-theme) — color palette inspiration
