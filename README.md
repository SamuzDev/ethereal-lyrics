# ethereal lyrics

A beautiful terminal application that displays synced lyrics for the music you're playing on Spotify.

![Preview](https://img.shields.io/badge/status-alpha-blue) ![Python](https://img.shields.io/badge/python-3.10+-green) ![License](https://img.shields.io/badge/license-MIT-purple)

## Features

- Real-time synced lyrics display
- Beautiful pastel color theme (Tokyo Night inspired)
- Gradient progress bar
- Current line highlighting
- Album info and playback status
- Free lyrics API (no API key required)
- Automatic lyrics caching

## Preview

```
┌─────────────────────────────────────────────────────────────────────┐
│  now playing                                                        │
│                                                                     │
│  Shape of You  ·  Ed Sheeran                                        │
│  from ÷ (Divide)                                                    │
│                                                                     │
│  ▶                                                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           lyrics                                     │
│                                                                     │
│       The club isn't the best place to find a lover                │
│       So the bar is where I go                                      │
│                                                                     │
│       ┌──────────────────────────────────────────────────┐          │
│       │  Me and my friends at the table doing shots      │          │
│       └──────────────────────────────────────────────────┘          │
│                                                                     │
│       Drinking fast and then we talk slow                               │
│       You come over and start up a conversation with just me        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

  01:23 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 03:54

┌─────────────────────────────────────────────────────────────────────┐
│                    q quit  ·  r refresh  ·  Esc back                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.10 or higher
- Spotify account
- Spotify Developer App credentials

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ethereal-lyrics.git
cd ethereal-lyrics
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create a Spotify Developer App:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Set redirect URI to `http://localhost:8888/callback`
   - Copy your Client ID and Client Secret

5. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Spotify credentials
```

## Usage

```bash
# Run the application
ethereal-lyrics

# Or run directly with Python
python -m src.main
```

### Controls

| Key    | Action           |
|--------|------------------|
| `q`    | Quit             |
| `r`    | Refresh lyrics   |
| `Esc`  | Back/Minimize    |

## Configuration

You can customize the application by editing the `.env` file:

```env
# Spotify credentials
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

## How It Works

1. **Spotify Integration**: Uses the official Spotify API to get your currently playing track
2. **Lyrics Fetching**: Fetches synced lyrics from LRCLib (free, no API key needed)
3. **Terminal UI**: Beautiful Rich-based interface with real-time updates

## Technologies Used

- **Python 3.10+**
- **Rich** - Beautiful terminal formatting
- **Spotipy** - Spotify Web API wrapper
- **HTTPX** - Modern HTTP client
- **Pydantic** - Settings management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [LRCLib](https://lrclib.net/) - Free lyrics API
- [Rich](https://github.com/Textualize/rich) - Terminal formatting library
- Tokyo Night theme for color inspiration
