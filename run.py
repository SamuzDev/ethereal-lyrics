"""Entry point for PyInstaller binary."""

import sys
from pathlib import Path

# Add src to path for absolute imports
src_dir = Path(__file__).parent / "src"
if src_dir.exists():
    sys.path.insert(0, str(src_dir))
else:
    # When running from PyInstaller bundle
    sys.path.insert(0, str(Path(sys._MEIPASS) / "src"))

from src.main import main

if __name__ == "__main__":
    main()