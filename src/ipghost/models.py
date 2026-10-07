"""Normalized internal data model.

The rest of the app (CLI, formatters, maps, batch engine) only talks to
IPInfo — never to raw provider field names. This is what makes it possible
to add Provider B/C later without touching anything else:

    raw provider JSON -> provider adapter -> IPInfo -> CLI/JSON/maps
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Geolocation:
    country: str | None = None
    country_code: str | None = None
    region: str | None = None
    region_code: str | None = None
    city: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None


@dataclass
class NetworkInfo:
    isp: str | None = None
    organization: str | None = None
    asn: str | None = None
    as_name: str | None = None
    hostname: str | None = None


@dataclass
class IPInfo:
    ip: str = ""
    ip_version: int = 4
    geolocation: Geolocation = field(default_factory=Geolocation)
    network: NetworkInfo = field(default_factory=NetworkInfo)
    google_maps_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        from .maps import build_maps_url

        url = self.google_maps_url
        if url is None:
            url = build_maps_url(
                self.geolocation.latitude, self.geolocation.longitude
            )
        return {
            "ip": self.ip,
            "ip_version": self.ip_version,
            "geolocation": asdict(self.geolocation),
            "network": asdict(self.network),
            "google_maps_url": url,
        }
