"""IP address validation built on the stdlib `ipaddress` module.

Public-only policy: the tool targets public routable addresses. Private,
loopback, link-local, multicast, reserved and unspecified addresses are
rejected with a clear reason and are never sent to the provider.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from .errors import InvalidIPError, NonPublicIPError

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address


@dataclass
class ValidatedIP:
    address: IPAddress
    version: int
    text: str


def parse_ip(raw: str) -> ValidatedIP:
    """Parse and validate syntax. Raises InvalidIPError on any bad input."""
    if raw is None:
        raise InvalidIPError("Empty IP address.")
    text = raw.strip().strip("[],").strip()
    if not text:
        raise InvalidIPError("Empty IP address.")
    # Reject obviously unsupported formats early (CIDR, URLs, hostnames).
    if "/" in text or " " in text:
        raise InvalidIPError(f"Invalid IP address: {raw.strip()!r}.")
    try:
        addr = ipaddress.ip_address(text)
    except ValueError as exc:
        raise InvalidIPError(f"Invalid IP address: {raw.strip()!r}.") from exc
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
