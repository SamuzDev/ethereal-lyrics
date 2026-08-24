"""Entry point for PyInstaller binary."""

import sys
import os
from pathlib import Path

HELP_TEXT = """ethereal-lyrics - synced lyrics in your terminal

Usage:
  ethereal-lyrics              Run the lyrics display
  ethereal-lyrics [OPTIONS]

Options:
  -l, --lyrics        Show raw lyrics data for current track
  -u, --update        Update to latest version
  -c, --check-update  Check for available updates
  -C, --color COLOR   Override lyric color (e.g. cyan, magenta)
  -h, --help          Show this help message

Environment Variables:
  LYRIC_OFFSET_MS     Lyric timing offset in ms (default: 1000)
  LYRIC_COLOR         Lyric text color (default: bold white)
  SPOTIFY_CLIENT_ID   Spotify API client ID (optional)
  SPOTIFY_CLIENT_SECRET Spotify API client secret (optional)
  MUSIXMATCH_API_KEY  Musixmatch API key (optional)

Examples:
  ethereal-lyrics
  ethereal-lyrics --lyrics
  ethereal-lyrics --update
  ethereal-lyrics --color cyan
  LYRIC_COLOR=magenta ethereal-lyrics
"""

# Add src to path for absolute imports
src_dir = Path(__file__).parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
elif hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, str(Path(sys._MEIPASS) / "src"))
else:
    print("Error: Cannot find source directory", file=sys.stderr)
    sys.exit(1)

# Parse arguments
args = sys.argv[1:]

if "-h" in args or "--help" in args:
    print(HELP_TEXT)
    sys.exit(0)

if "-u" in args or "--update" in args:
    try:
        from src.updater import check_for_updates
        check_for_updates(silent=False)
    except Exception as e:
        print(f"Update failed: {e}", file=sys.stderr)
    sys.exit(0)

if "-c" in args or "--check-update" in args:
    try:
        from src.updater import get_current_version, get_latest_version, _parse_version
        current = get_current_version()
        latest = get_latest_version()
        if latest and _parse_version(current) < _parse_version(latest):
            print(f"Update available: v{current} \u2192 v{latest}")
            print(f"Run: ethereal-lyrics --update")
            sys.exit(1)
        # Silent if up to date
    except Exception as e:
        print(f"Check failed: {e}", file=sys.stderr)
    sys.exit(0)

if "-l" in args or "--lyrics" in args:
    try:
        from src.main import show_lyrics_debug
        show_lyrics_debug()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    sys.exit(0)

# Handle --color / -C
color_override = None
for i, arg in enumerate(args):
    if arg in ("-C", "--color") and i + 1 < len(args):
        color_override = args[i + 1]
        os.environ["LYRIC_COLOR"] = color_override
        break

# Silent update check on startup
try:
    from src.updater import check_for_updates
    check_for_updates(silent=True)
except Exception:
    pass

from src.main import main

if __name__ == "__main__":
    main()
