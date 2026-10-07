"""Terminal UI — Kali/OSINT aesthetic, ASCII-first.

Rules this module follows:
- ASCII only for art, separators and status tokens (never decorative
  Unicode, so terminal codecs cannot mangle the interface).
- ANSI colors are decorative only: every string is also correct with
  colors disabled (--no-color / non-tty).
- This module formats data; it never validates, fetches or sanitizes.
"""

from __future__ import annotations

from .models import IPInfo

BANNER_ART = (
    "   ___ ____   ____ ____  _   _  ___  ____ _____",
    "  |_ _|  _ \\ / ___/ ___|| | | |/ _ \\ / ___|_   _|",
    "   | || |_) | |  | |  _ | |_| | | | | |  _  | |",
    "   | ||  __/| |__| |_| ||  _  | |_| | |_| | | |",
    "  |___|_|    \\____\\____||_| |_|\\___/ \\____|_|",
)

BANNER_SUBTITLE = "GLOBAL IP INTELLIGENCE & GEOLOCATION CLI"

APPROX_NOTE = (
    "[!] NOTE\n"
    "    IP geolocation is approximate.\n"
    "    It does not identify an exact physical address,\n"
    "    person, or real-time device location."
)


class Palette:
    """ANSI colors behind one switch. Disabled == plain ASCII text."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def brand(self, text: str) -> str:
        return self.wrap("1;33", text)

    def data(self, text: str) -> str:
        return self.wrap("36", text)

    def token_ok(self) -> str:
        return self.wrap("1;32", "[+]")

    def token_info(self) -> str:
        return self.wrap("36", "[::]")

    def token_ask(self) -> str:
        return self.wrap("1;33", "[?]")

    def token_in(self) -> str:
        return self.wrap("37", "[-]")

    def token_warn(self) -> str:
        return self.wrap("1;31", "[!]")

    def token_error(self) -> str:
        return self.wrap("1;31", "[ERROR]")

    # Backwards-compatible helpers (kept small on purpose).
    def title(self, text: str) -> str:
        return self.brand(text)

    def section(self, text: str) -> str:
        return self.brand(text)

    def warn(self, text: str) -> str:
        return self.wrap("1;31", text)

    def error(self, text: str) -> str:
        return self.wrap("1;31", text)


def colors_enabled(no_color: bool = False) -> bool:
    import os
    import sys

    if no_color:
        return False
    if os.environ.get("NO_COLOR", "") != "":
        return False
    if os.environ.get("IPGHOST_NO_COLOR", "").lower() in ("1", "true", "yes"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _v(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return str(value)
    text = str(value).strip()
    return text if text else "N/A"


def ascii_banner(p: Palette) -> str:
    width = max(len(line) for line in BANNER_ART)
    art = "\n".join(p.brand(line) for line in BANNER_ART)
    sub = p.data(BANNER_SUBTITLE.center(width))
    return f"{art}\n{sub}"


def banner(p: Palette) -> str:
    """Legacy name kept for callers; returns the ASCII banner."""
    return ascii_banner(p)


def startup(p: Palette, version: str) -> str:
    lines = [
        "",
        ascii_banner(p),
        "",
        f"{p.token_info()} Global IP Intelligence & Geolocation CLI",
        f"{p.token_info()} Version {version}",
        f"{p.token_ok()} Status: Ready",
        "",
    ]
    return "\n".join(lines)


def report_banner(p: Palette) -> str:
    """Legacy name kept for callers; no giant boxes anymore."""
    return ascii_banner(p)


def stage_line(p: Palette, stage: str) -> str | None:
    """Map a real lookup stage to one honest progress line."""
    if stage == "validating":
        return f"{p.token_info()} Validating IP..."
    if stage == "querying":
        return f"{p.token_info()} Querying GeoIP provider..."
    if stage == "cached":
        return f"{p.token_info()} Loading cached result..."
    if stage == "done":
        return f"{p.token_ok()} Lookup completed."
    return None


def format_report(info: IPInfo, p: Palette) -> str:
    g = info.geolocation
    n = info.network
    version = "IPv6" if info.ip_version == 6 else "IPv4"
    lines = [
        "",
        f"{p.token_ok()} {p.brand('IP INFORMATION')}",
        f"    Address      : {p.data(info.ip)}",
        f"    Version      : {p.data(version)}",
        f"    Type         : {p.data('Public')}",
        "",
        f"{p.token_ok()} {p.brand('GEOLOCATION')}",
        f"    Country      : {p.data(_v(g.country))}",
        f"    Country Code : {p.data(_v(g.country_code))}",
        f"    Region       : {p.data(_v(g.region))}",
        f"    Region Code  : {p.data(_v(g.region_code))}",
        f"    City         : {p.data(_v(g.city))}",
        f"    Postal Code  : {p.data(_v(g.postal_code))}",
        f"    Latitude     : {p.data(_v(g.latitude))}",
        f"    Longitude    : {p.data(_v(g.longitude))}",
        f"    Timezone     : {p.data(_v(g.timezone))}",
        "",
        f"{p.token_ok()} {p.brand('NETWORK')}",
        f"    ISP          : {p.data(_v(n.isp))}",
        f"    Organization : {p.data(_v(n.organization))}",
        f"    ASN          : {p.data(_v(n.asn))}",
        f"    AS Name      : {p.data(_v(n.as_name))}",
        f"    Hostname     : {p.data(_v(n.hostname))}",
        "",
    ]
    if info.google_maps_url:
        lines.append(f"{p.token_ok()} {p.brand('GOOGLE MAPS')}")
        lines.append("")
        lines.append(f"    {p.data(info.google_maps_url)}")
        lines.append("")
    else:
        lines.append(f"{p.token_warn()} Google Maps location unavailable.")
        lines.append("")
    lines.append(p.token_warn() + " NOTE")
    lines.append("    IP geolocation is approximate.")
    lines.append("    It does not identify an exact physical address,")
    lines.append("    person, or real-time device location.")
    lines.append("")
    return "\n".join(lines)


def interactive_menu(p: Palette, maps_available: bool) -> str:
    lines = [
        "",
        f"{p.token_info()} Actions",
        "",
        "[01] Analyze another IP",
    ]
    if maps_available:
        lines.append("[02] Open location in Google Maps")
    else:
        lines.append("[02] Open location in Google Maps (unavailable)")
    lines += [
        "[03] Export JSON",
        "[04] Save report",
        "[00] Exit",
        "",
        f"{p.token_ask()} Select an option:",
    ]
    return "\n".join(lines)


def input_prompt(p: Palette) -> str:
    return f"{p.token_ask()} Enter public IP address:\n{p.token_in()} "


def batch_header(p: Palette, total: int) -> str:
    return f"{p.token_info()} Processing {total} IP addresses..."


def batch_item(p: Palette, index: int) -> str:
    return f"{p.data(f'[{index:02d}]')}"


def batch_summary(p: Palette, ok: int, failed: int) -> str:
    return (
        f"{p.token_info()} Completed: {ok}\n"
        f"{p.token_info()} Failed: {failed}"
    )
