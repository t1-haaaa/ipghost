"""Validator seams: valid v4/v6, invalid, private, loopback, reserved."""

import pytest

from ipghost.errors import InvalidIPError, NonPublicIPError
from ipghost.validators import ensure_public, parse_ip


def test_valid_ipv4():
    parsed = parse_ip("8.8.8.8")
    assert parsed.version == 4
    assert parsed.text == "8.8.8.8"


def test_valid_ipv6():
    parsed = parse_ip("2001:4860:4860::8888")
    assert parsed.version == 6


def test_invalid_ip_rejected():
    with pytest.raises(InvalidIPError):
        parse_ip("999.999.999.999")
    with pytest.raises(InvalidIPError):
        parse_ip("not-an-ip")
    with pytest.raises(InvalidIPError):
        parse_ip("")
    with pytest.raises(InvalidIPError):
        parse_ip("8.8.8.8/24")


def test_private_rejected_with_reason():
    with pytest.raises(NonPublicIPError):
        ensure_public("192.168.1.1")
    with pytest.raises(NonPublicIPError):
        ensure_public("10.0.0.1")


def test_loopback_reserved_rejected():
    with pytest.raises(NonPublicIPError):
        ensure_public("127.0.0.1")
    with pytest.raises(NonPublicIPError):
        ensure_public("::1")


def test_public_passes():
    assert ensure_public("8.8.8.8").version == 4
    assert ensure_public("1.1.1.1").version == 4
