"""Entry point for PyInstaller binary."""

import sys
import os
from pathlib import Path

# Add src to path for absolute imports
src_dir = Path(__file__).parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
elif hasattr(sys, '_MEIPASS'):
    sys.path.insert(0, str(Path(sys._MEIPASS) / "src"))
else:
    print("Error: Cannot find source directory", file=sys.stderr)
    sys.exit(1)

# Handle CLI flags
if "--update" in sys.argv:
    try:
        from src.updater import check_for_updates
        check_for_updates(silent=False)
    except Exception as e:
        print(f"Update failed: {e}", file=sys.stderr)
    sys.exit(0)

if "--check-update" in sys.argv:
    try:
        from src.updater import get_current_version, get_latest_version, _parse_version
        current = get_current_version()
        latest = get_latest_version()
        if latest and _parse_version(current) < _parse_version(latest):
            print(f"Update available: v{current} \u2192 v{latest}")
            print(f"Run: ethereal-lyrics --update")
        else:
            print(f"You're up to date (v{current})")
    except Exception as e:
        print(f"Check failed: {e}", file=sys.stderr)
    sys.exit(0)

if "--lyrics" in sys.argv:
    try:
        from src.main import show_lyrics_debug
        show_lyrics_debug()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    sys.exit(0)

# Silent update check on startup
try:
    from src.updater import check_for_updates
    check_for_updates(silent=True)
except Exception:
    pass

from src.main import main

if __name__ == "__main__":
    main()
