"""Entry point for PyInstaller binary."""

import sys
import os
from pathlib import Path

# Add src to path for absolute imports
src_dir = Path(__file__).parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
elif hasattr(sys, '_MEIPASS'):
    # Running from PyInstaller bundle
    sys.path.insert(0, str(Path(sys._MEIPASS) / "src"))
else:
    print("Error: Cannot find source directory", file=sys.stderr)
    sys.exit(1)

# Check for updates
try:
    from src.updater import check_for_updates
    if "--update" in sys.argv:
        check_for_updates(silent=False)
        sys.exit(0)
    elif "--check-update" in sys.argv:
        from src.updater import get_current_version, get_latest_version
        from src.updater import _parse_version
        current = get_current_version()
        latest = get_latest_version()
        if latest and _parse_version(current) < _parse_version(latest):
            print(f"Update available: v{current} \u2192 v{latest}")
            print(f"Run: ethereal-lyrics --update")
        else:
            print(f"You're up to date (v{current})")
        sys.exit(0)
    else:
        # Silent check in background
        try:
            check_for_updates(silent=True)
        except Exception:
            pass
except Exception:
    pass

from src.main import main

if __name__ == "__main__":
    main()