"""JSON contract: keys, nulls, no ANSI."""

import json

from ipghost.models import IPInfo


def test_json_contract():
    info = IPInfo(ip="1.1.1.1", ip_version=4)
    data = info.to_dict()
    assert set(data.keys()) == {
        "ip",
        "ip_version",
        "geolocation",
        "network",
        "google_maps_url",
    }
    assert set(data["geolocation"].keys()) == {
        "country",
        "country_code",
        "region",
        "region_code",
        "city",
        "postal_code",
        "latitude",
        "longitude",
        "timezone",
    }
    text = json.dumps(data)
    assert "\x1b" not in text
    # Missing fields are null, not crash.
    assert data["geolocation"]["country"] is None
    assert data["google_maps_url"] is None
