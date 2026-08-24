"""Entry point for PyInstaller binary."""

import sys
import os
from pathlib import Path

# Add src to path for absolute imports
src_dir = Path(__file__).parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
else:
    # When running from PyInstaller bundle
    sys.path.insert(0, str(Path(sys._MEIPASS) / "src"))

# Check for updates (non-blocking, silent)
try:
    from src.updater import check_for_updates
    if "--update" in sys.argv:
        check_for_updates(silent=False)
        sys.exit(0)
    elif "--check-update" in sys.argv:
        from src.updater import get_current_version, get_latest_version
        current = get_current_version()
        latest = get_latest_version()
        if latest and current < latest:
            print(f"Update available: v{current} → v{latest}")
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