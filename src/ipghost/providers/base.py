"""Provider interface — the seam every adapter satisfies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import IPInfo


class GeoIPProvider(ABC):
    """Lookup an IP and return a normalized IPInfo."""

    name: str = "base"

    @abstractmethod
    def lookup(self, ip: str) -> IPInfo:
        raise NotImplementedError
