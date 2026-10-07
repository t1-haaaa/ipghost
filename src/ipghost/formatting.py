"""Terminal formatting. Colors are decorative only — never required."""

from __future__ import annotations

import os
import sys

from .models import IPInfo

_APPROX_NOTE = (
    "[!] NOTE\n"
    "    IP geolocation is approximate.\n"
    "    It does not identify an exact physical address,\n"
    "    person, or real-time device location."
)


class Palette:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def title(self, text: str) -> str:
        return self.wrap("1;36", text)

    def section(self, text: str) -> str:
        return self.wrap("1;32", text)

    def warn(self, text: str) -> str:
        return self.wrap("1;33", text)

    def error(self, text: str) -> str:
        return self.wrap("1;31", text)


def colors_enabled(no_color: bool = False) -> bool:
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


def banner(p: Palette) -> str:
    top = "╔══════════════════════════════════════════════════════════╗"
    mid1 = "║                         IPGHOST                          ║"
    mid2 = "║             GLOBAL IP INTELLIGENCE CLI                   ║"
    bot = "╚══════════════════════════════════════════════════════════╝"
    return "\n".join(
        [p.title(top), p.title(mid1), p.title(mid2), p.title(bot)]
    )


def report_banner(p: Palette) -> str:
    top = "╔══════════════════════════════════════════════════════════╗"
    mid1 = "║                         IPGHOST                          ║"
    mid2 = "║             GLOBAL IP INTELLIGENCE REPORT                ║"
    bot = "╚══════════════════════════════════════════════════════════╝"
    return "\n".join(
        [p.title(top), p.title(mid1), p.title(mid2), p.title(bot)]
    )


def format_report(info: IPInfo, p: Palette) -> str:
    g = info.geolocation
    n = info.network
    lines = [
        "",
        report_banner(p),
        "",
        p.section("[+] IP ADDRESS"),
        f"    {info.ip}",
        "",
        p.section("[+] GEOLOCATION"),
        f"    Country      : {_v(g.country)}",
        f"    Country Code : {_v(g.country_code)}",
        f"    Region       : {_v(g.region)}",
        f"    Region Code  : {_v(g.region_code)}",
        f"    City         : {_v(g.city)}",
        f"    Postal Code  : {_v(g.postal_code)}",
        f"    Latitude     : {_v(g.latitude)}",
        f"    Longitude    : {_v(g.longitude)}",
        f"    Timezone     : {_v(g.timezone)}",
        "",
        p.section("[+] NETWORK"),
        f"    ISP          : {_v(n.isp)}",
        f"    Organization : {_v(n.organization)}",
        f"    ASN          : {_v(n.asn)}",
        f"    AS Name      : {_v(n.as_name)}",
        f"    Hostname     : {_v(n.hostname)}",
        "",
    ]
    if info.google_maps_url:
        lines.append(p.section("[+] GOOGLE MAPS"))
        lines.append("")
        lines.append(f"    {info.google_maps_url}")
        lines.append("")
    else:
        lines.append(p.warn("[!] Google Maps location unavailable."))
        lines.append("")
    lines.append(p.warn(_APPROX_NOTE))
    lines.append("")
    return "\n".join(lines)


def interactive_menu(p: Palette, maps_available: bool) -> str:
    lines = [
        "══════════════════════════════════════════════════════════",
        "",
        "[1] Analyze another IP",
    ]
    if maps_available:
        lines.append("[2] Open location in Google Maps")
    else:
        lines.append("[2] Open location in Google Maps (unavailable)")
    lines += [
        "[3] Export JSON",
        "[4] Save report",
        "[0] Exit",
        "",
        "Select: ",
    ]
    return "\n".join(lines)
