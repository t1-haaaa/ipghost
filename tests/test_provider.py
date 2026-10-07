"""Provider seam with mocked HTTP — no real API calls."""

from ipghost import http as http_client
from ipghost.providers.primary import IPWhoIsProvider, normalize


def _fake_ok(url, timeout=None):
    class Resp:
        status = 200

        def read(self):
            import json

            return json.dumps(
                {
                    "ip": "8.8.8.8",
                    "success": True,
                    "type": "IPv4",
                    "country": "United States",
                    "country_code": "US",
                    "region": "California",
                    "region_code": "CA",
                    "city": "Mountain View",
                    "postal": "94043",
                    "latitude": 37.386,
                    "longitude": -122.0838,
                    "timezone": {"id": "America/Los_Angeles"},
                    "connection": {"asn": 15169, "org": "Google LLC", "isp": "Google LLC"},
                }
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    return Resp()


def test_normalize_ok(monkeypatch):
    monkeypatch.setattr(http_client.urllib.request, "urlopen", _fake_ok)
    provider = IPWhoIsProvider(timeout=5)
    info = provider.lookup("8.8.8.8")
    assert info.ip == "8.8.8.8"
    assert info.ip_version == 4
    assert info.geolocation.country == "United States"
    assert info.network.asn == "AS15169"
    assert info.google_maps_url is not None
    assert "google.com/maps" in info.google_maps_url


def test_rate_limit(monkeypatch):
    import urllib.error

    def _boom(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many", {}, None)

    monkeypatch.setattr(http_client.urllib.request, "urlopen", _boom)
    provider = IPWhoIsProvider(timeout=5)
    import pytest

    from ipghost.errors import RateLimitError

    with pytest.raises(RateLimitError):
        provider.lookup("8.8.8.8")


def test_malformed_json(monkeypatch):
    def _bad(url, timeout=None):
        class Resp:
            status = 200

            def read(self):
                return b"not json{{"

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return Resp()

    monkeypatch.setattr(http_client.urllib.request, "urlopen", _bad)
    provider = IPWhoIsProvider(timeout=5)
    import pytest

    from ipghost.errors import BadResponseError

    with pytest.raises(BadResponseError):
        provider.lookup("8.8.8.8")


def test_missing_fields_do_not_crash():
    info = normalize("9.9.9.9", {"ip": "9.9.9.9", "success": True, "type": "IPv4"})
    assert info.ip == "9.9.9.9"
    assert info.geolocation.country is None
    assert info.google_maps_url is None
