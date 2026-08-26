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
  -v, --version       Show current version
  -C, --color COLOR   Override lyric color (e.g. cyan, magenta, 196)
  -W, --words N       Number of words to show at once (default: 1)
  -h, --help          Show this help message

Environment Variables:
  LYRIC_OFFSET_MS     Lyric timing offset in ms (default: 0)
  LYRIC_COLOR         Lyric text color (default: bold white)
  SPOTIFY_CLIENT_ID   Spotify API client ID (optional)
  SPOTIFY_CLIENT_SECRET Spotify API client secret (optional)
  MUSIXMATCH_API_KEY  Musixmatch API key (optional)

Examples:
  ethereal-lyrics
  ethereal-lyrics --lyrics
  ethereal-lyrics --update
  ethereal-lyrics --color cyan
  ethereal-lyrics -C 196
  ethereal-lyrics -C 'bold magenta'
  LYRIC_COLOR=magenta ethereal-lyrics
"""

COLOR_HELP = """Color Options:
  -C, --color COLOR   Set lyric text color

  Named colors:
    red, green, blue, cyan, magenta, yellow, white
    bright_red, bright_green, bright_blue, bright_cyan, bright_magenta, bright_yellow

  256-color (by number 1-256):
    1       red             196     bright red
    2       green           46      bright green
    3       yellow          226     bright yellow
    4       blue            21      bright blue
    5       magenta         201     bright magenta
    6       cyan            51      bright cyan
    7       white           231     bright white
    8       gray            240     dark gray

  Hex/RGB:
    '#ff6432'               'rgb(255,100,50)'

  Bold/italic:
    'bold cyan'             'italic magenta'

  Default: bold white
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

# Handle -C -h (color help)
if "-C" in args and "-h" in args:
    print(COLOR_HELP)
    sys.exit(0)

if "-h" in args or "--help" in args:
    print(HELP_TEXT)
    sys.exit(0)

if "-v" in args or "--version" in args:
    from src.updater import get_current_version
    print(f"ethereal-lyrics v{get_current_version()}")
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

if "-l" in args or "--lyrics" in args:
    try:
        from src.main import show_lyrics_debug
        show_lyrics_debug()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    sys.exit(0)

# Handle --color / -C
color_override = None
color_arg_found = False
for i, arg in enumerate(args):
    if arg in ("-C", "--color"):
        color_arg_found = True
        if i + 1 < len(args):
            color_val = args[i + 1]
            # Accept numbers 1-256
            if color_val.isdigit() and 1 <= int(color_val) <= 256:
                color_override = f"color({color_val})"
            else:
                color_override = color_val
            os.environ["LYRIC_COLOR"] = color_override
        break

# Handle --words / -W
for i, arg in enumerate(args):
    if arg in ("-W", "--words"):
        if i + 1 < len(args) and args[i + 1].isdigit():
            word_count = max(1, int(args[i + 1]))
            os.environ["LYRIC_WORDS"] = str(word_count)
        break

# Check for unknown arguments
valid_flags = {"-l", "--lyrics", "-u", "--update", "-c", "--check-update",
               "-v", "--version", "-C", "--color", "-W", "--words", "-h", "--help"}

# Build set of args that are values for flags (e.g., value after -C/--color, -W/--words)
skip_args = set()
for i, arg in enumerate(args):
    if arg in ("-C", "--color", "-W", "--words") and i + 1 < len(args):
        skip_args.add(args[i + 1])

for arg in args:
    if arg.startswith("-") and arg not in valid_flags and arg not in skip_args:
        print(f"\033[0;31m\u2717\033[0m Unknown option: \033[1;33m{arg}\033[0m")
        print("  Run 'ethereal-lyrics -h' for usage information.")
        sys.exit(1)

# Silent update check on startup
try:
    from src.updater import check_for_updates
    check_for_updates(silent=True)
except Exception:
    pass

from src.main import main

if __name__ == "__main__":
    main()
