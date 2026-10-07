"""IP address validation built on the stdlib `ipaddress` module.

Public-only policy: the tool targets public routable addresses. Private,
loopback, link-local, multicast, reserved and unspecified addresses are
rejected with a clear reason and are never sent to the provider.
"""

from __future__ import annotations

import ipaddress
import unicodedata
from dataclasses import dataclass

from .errors import InvalidIPError, NonPublicIPError

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


@dataclass
class ValidatedIP:
    address: IPAddress
    version: int
    text: str


# Invisible characters that commonly sneak in via copy-paste, BOM-prefixed
# files, RTL/bidi terminals, or stdin codec mismatches (e.g. C1 controls such
# as U+0096/U+0083). They are never part of an IPv4/IPv6 literal, so removing
# them from the EDGES is safe. Anything invisible left INSIDE the text still
# fails validation — we never mask real content.
_EDGE_STRIP_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})
# U+FFFD appears when undecodable stdin bytes are decoded with errors="replace";
# it is never part of an address.
_EDGE_STRIP_EXTRA = frozenset({"\ufffd"})


def clean_ip_text(raw: object) -> str:
    """Return user input with surrounding whitespace/invisibles removed.

    Only the edges are touched; interior content is returned verbatim so a
    genuinely invalid address can never become valid silently.
    """
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise InvalidIPError("Invalid IP address.")
    text = raw.strip()
    # Strip "[...]" wrappers first (existing behaviour, e.g. "[::1]").
    text = text.strip("[],").strip()
    start, end = 0, len(text)
    while start < end and (
        unicodedata.category(text[start]) in _EDGE_STRIP_CATEGORIES
        or text[start] in _EDGE_STRIP_EXTRA
    ):
        start += 1
    while end > start and (
        unicodedata.category(text[end - 1]) in _EDGE_STRIP_CATEGORIES
        or text[end - 1] in _EDGE_STRIP_EXTRA
    ):
        end -= 1
    return text[start:end].strip()


def parse_ip(raw: str) -> ValidatedIP:
    """Parse and validate syntax. Raises InvalidIPError on any bad input."""
    if raw is not None and not isinstance(raw, str):
        raise InvalidIPError("Invalid IP address.")
    text = clean_ip_text(raw)
    if not text:
        raise InvalidIPError("Empty IP address.")
    # Reject obviously unsupported formats early (CIDR, URLs, hostnames).
    if "/" in text or " " in text:
        raise InvalidIPError("Invalid IP address.")
    try:
        addr = ipaddress.ip_address(text)
    except ValueError as exc:
        raise InvalidIPError("Invalid IP address.") from exc
    return ValidatedIP(address=addr, version=addr.version, text=str(addr))


def public_routability_reason(addr: IPAddress) -> str | None:
    """Return a human reason when addr is NOT public, else None."""
    # Order matters for the clearest message.
    if addr.is_loopback:
        return "loopback address"
    if addr.is_private:
        # ipaddress marks some reserved ranges as private too; check the
        # more specific cases first where possible. Keep message simple.
        return "private address"
    if addr.is_link_local:
        return "link-local address"
    if addr.is_multicast:
        return "multicast address"
    if addr.is_reserved:
        return "reserved address"
    if addr.is_unspecified:
        return "unspecified address"
    return None


def ensure_public(raw: str) -> ValidatedIP:
    """Parse + enforce public-only policy. Never sends bad IP to provider."""
    parsed = parse_ip(raw)
    reason = public_routability_reason(parsed.address)
    if reason is not None:
        raise NonPublicIPError(
            f"{parsed.text} is not a public routable IP ({reason})."
        )
    return parsed
