"""Auto-update mechanism for ethereal-lyrics binary."""

import os
import sys
import urllib.request
import json
from pathlib import Path

VERSION = "0.5.29"
REPO = "SamuzDev/ethereal-lyrics"
GITHUB_API = f"https://api.github.com/repos/{REPO}/releases"


def get_current_version() -> str:
    """Return the current version."""
    return VERSION


def get_latest_version() -> str | None:
    """Check GitHub for the latest non-draft release version."""
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            releases = json.loads(resp.read())
            for release in releases:
                if not release.get("draft", False):
                    tag = release.get("tag_name", "")
                    if tag:
                        return tag.lstrip("v")
            return None
    except Exception:
        return None


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into comparable tuple."""
    try:
        return tuple(int(x) for x in version.split("."))
    except (ValueError, AttributeError):
        return (0,)


def get_platform_binary_name() -> str:
    """Get the binary name for the current platform."""
    import platform
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif machine in ("armv7l", "armhf"):
        arch = "armv7"
    else:
        arch = machine
    
    return f"ethereal-lyrics-{system}-{arch}"


def download_update(version: str) -> bool:
    """Download and install the latest binary."""
    binary_name = get_platform_binary_name()
    url = f"https://github.com/{REPO}/releases/download/v{version}/{binary_name}"
    
    # Get current binary path
    if getattr(sys, 'frozen', False):
        current_path = Path(sys.executable)
    else:
        # Running from source - don't overwrite src directory
        print("  Cannot auto-update from source. Use 'pip install' instead.")
        return False
    
    # Download to temp file
    temp_path = current_path.parent / f"{binary_name}.tmp"
    
    try:
        print(f"  Downloading v{version}...")
        
        def show_progress(block_num: int, block_size: int, total_size: int) -> None:
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, (downloaded / total_size) * 100)
                bar_len = 30
                filled = int(bar_len * downloaded / total_size)
                bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
                print(f"\r  [{bar}] {percent:.1f}%", end="", flush=True)
            else:
                print(f"\r  Downloaded: {downloaded / 1024 / 1024:.1f} MB", end="", flush=True)
        
        urllib.request.urlretrieve(url, temp_path, reporthook=show_progress)
        print()
        
        temp_path.chmod(0o755)
        
        # Replace current binary
        old_path = current_path.parent / f"{current_path.name}.old"
        if old_path.exists():
            old_path.unlink()
        current_path.rename(old_path)
        temp_path.rename(current_path)
        old_path.unlink(missing_ok=True)
        
        return True
    except Exception as e:
        print(f"  Update failed: {e}")
        temp_path.unlink(missing_ok=True)
        return False


def check_for_updates(silent: bool = True) -> bool:
    """Check for updates and optionally install them.
    
    Returns True if an update was installed.
    """
    current = get_current_version()
    latest = get_latest_version()
    
    if latest is None:
        return False
    
    if _parse_version(current) >= _parse_version(latest):
        return False
    
    if not silent:
        print(f"\n  Update available: v{current} \u2192 v{latest}")
        response = input("  Install update? [y/N] ").strip().lower()
        if response != 'y':
            return False
    
    if download_update(latest):
        if not silent:
            print(f"  Updated to v{latest}! Restart to use the new version.")
        return True
    
    return False


if __name__ == "__main__":
    check_for_updates(silent=False)