"""Google Maps URL helpers — validation first, URL second.

The URL is always built locally from validated floats. We never pass a
provider-supplied URL through to the shell/browser.
"""

from __future__ import annotations

import shutil
import subprocess

Number = int | float | str | None


def _to_float(value: Number) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def valid_coordinates(latitude: Number, longitude: Number) -> bool:
    lat = _to_float(latitude)
    lon = _to_float(longitude)
    if lat is None or lon is None:
        return False
    # Reject NaN/inf explicitly.
    if lat != lat or lon != lon:
        return False
    if lat in (float("inf"), float("-inf")):
        return False
    if lon in (float("inf"), float("-inf")):
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def build_maps_url(latitude: Number, longitude: Number) -> str | None:
    if not valid_coordinates(latitude, longitude):
        return None
    lat = _to_float(latitude)
    lon = _to_float(longitude)
    assert lat is not None and lon is not None
    return f"https://www.google.com/maps?q={lat},{lon}"


def open_in_browser(url: str) -> tuple[bool, str]:
    """Open url safely (no shell). Returns (opened, message)."""
    if not url.startswith("https://www.google.com/maps?q="):
        return False, "Refusing to open an unexpected URL."
    opener = shutil.which("xdg-open")
    if opener is None:
        # macOS / Windows fallbacks — best effort, Linux-first.
        for candidate in ("gio", "sensible-browser", "x-www-browser"):
            opener = shutil.which(candidate)
            if opener:
                break
    if opener is None:
        return False, "Could not open browser automatically."
    try:
        subprocess.run(
            [opener, url],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
        )
        return True, "Browser opened."
    except Exception:
        return False, "Could not open browser automatically."
