"""Primary provider: ipwho.is (free, HTTPS, no key, IPv4+IPv6).

Docs: https://ipwho.is/ — GET https://ipwho.is/{ip}
"""

from __future__ import annotations

from typing import Any

from .. import http as http_client
from ..errors import BadResponseError, NotFoundError
from ..maps import build_maps_url
from ..models import Geolocation, IPInfo, NetworkInfo
from ..validators import ensure_public
from .base import GeoIPProvider

_API = "https://ipwho.is/"


def _str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip()
    return text or None


def _float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def normalize(ip_text: str, payload: Any) -> IPInfo:
    """Convert raw provider JSON into the internal IPInfo model."""
    if not isinstance(payload, dict):
        raise BadResponseError("Provider returned an unexpected response shape.")
    if payload.get("success") is False:
        message = _str(payload.get("message")) or "Provider has no data for this IP."
        raise NotFoundError(message)

    connection = payload.get("connection")
    if connection is not None and not isinstance(connection, dict):
        connection = {}
    connection = connection or {}

    timezone = payload.get("timezone")
    if isinstance(timezone, dict):
        tz = _str(timezone.get("id"))
    else:
        tz = _str(timezone)

    asn_raw = connection.get("asn")
    asn: str | None
    if asn_raw is None:
        asn = None
    elif isinstance(asn_raw, int):
        asn = f"AS{asn_raw}"
    else:
        text = _str(asn_raw)
        asn = text if text is None else (text if text.upper().startswith("AS") else text)

    lat = _float(payload.get("latitude"))
    lon = _float(payload.get("longitude"))

    # Validate response types — never let provider data crash the app.
    ip_value = _str(payload.get("ip")) or ip_text
    type_value = _str(payload.get("type")) or ""
    version = 6 if type_value == "IPv6" else (4 if type_value == "IPv4" else 0)
    if version == 0:
        version = 6 if ":" in ip_value else 4

    geo = Geolocation(
        country=_str(payload.get("country")),
        country_code=_str(payload.get("country_code")),
        region=_str(payload.get("region")),
        region_code=_str(payload.get("region_code")),
        city=_str(payload.get("city")),
        postal_code=_str(payload.get("postal")),
        latitude=lat,
        longitude=lon,
        timezone=tz,
    )
    net = NetworkInfo(
        isp=_str(connection.get("isp")),
        organization=_str(connection.get("org")),
        asn=asn,
        as_name=None,
        hostname=_str(connection.get("domain")),
    )
    return IPInfo(
        ip=ip_value,
        ip_version=version,
        geolocation=geo,
        network=net,
        google_maps_url=build_maps_url(lat, lon),
    )


class IPWhoIsProvider(GeoIPProvider):
    name = "ipwho.is"

    def __init__(self, timeout: float = 10.0, debug: bool = False) -> None:
        self.timeout = timeout
        self.debug = debug

    def lookup(self, ip: str) -> IPInfo:
        validated = ensure_public(ip)
        payload = http_client.get_json(
            f"{_API}{validated.text}", timeout=self.timeout, debug=self.debug
        )
        return normalize(validated.text, payload)
