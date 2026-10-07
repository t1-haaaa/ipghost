"""Maps seam: validation, URL generation, range checks."""

from ipghost.maps import build_maps_url, valid_coordinates


def test_valid_coordinates():
    assert valid_coordinates(45.5231, -122.6765) is True
    assert valid_coordinates(-90, -180) is True
    assert valid_coordinates(90, 180) is True


def test_invalid_coordinates():
    assert valid_coordinates(91, 0) is False
    assert valid_coordinates(0, 181) is False
    assert valid_coordinates(None, 0) is False
    assert valid_coordinates("abc", "def") is False


def test_url_generation():
    url = build_maps_url(45.5231, -122.6765)
    assert url == "https://www.google.com/maps?q=45.5231,-122.6765"


def test_url_none_when_invalid():
    assert build_maps_url(None, None) is None
    assert build_maps_url(999, 999) is None
