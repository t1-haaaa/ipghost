"""Regression tests for terminal/input-encoding handling.

Covers the reported symptom: input arriving with control/format garbage in
front of a valid IP (copy-paste / stdin codec mismatch) must resolve to the
intended public IP, while genuinely invalid input stays invalid and error
messages stay free of escape sequences.

All special characters are built with chr() so this file stays pure ASCII
with no literal invisible characters.
"""

import pytest

from ipghost.cli import _friendly_error
from ipghost.errors import InvalidIPError
from ipghost.validators import clean_ip_text, ensure_public, parse_ip

C1_PREFIX = chr(0x96) + chr(0x83) + chr(0x96)  # reported symptom
RLM = chr(0x200F)
LRM = chr(0x200E)
BOM = chr(0xFEFF)
NBSP = chr(0x00A0)
ZWSP = chr(0x200B)
REPLACEMENT = chr(0xFFFD)


def test_reported_case_control_prefix():
    poisoned = C1_PREFIX + "35.94.45.221"
    assert parse_ip(poisoned).text == "35.94.45.221"
    assert ensure_public(poisoned).text == "35.94.45.221"


def test_target_ips_plain():
    for ip in ("35.94.45.221", "8.8.8.8", "1.1.1.1"):
        assert ensure_public(ip).version == 4
    assert ensure_public("2001:4860:4860::8888").version == 6


def test_padded_and_bidi_edges():
    assert parse_ip(" 35.94.45.221 ").text == "35.94.45.221"
    assert parse_ip(RLM + "35.94.45.221" + LRM).text == "35.94.45.221"
    assert parse_ip(BOM + "8.8.8.8").text == "8.8.8.8"
    assert parse_ip(NBSP + "1.1.1.1" + NBSP).text == "1.1.1.1"
    assert parse_ip(REPLACEMENT + "2001:4860:4860::8888" + "\n").version == 6


def test_interior_garbage_stays_invalid():
    with pytest.raises(InvalidIPError):
        parse_ip("35.94." + ZWSP + "45.221")
    with pytest.raises(InvalidIPError):
        parse_ip("8.8.8.8 extra")
    with pytest.raises(InvalidIPError):
        parse_ip("--8.8.8.8")
    with pytest.raises(InvalidIPError):
        parse_ip("not-an-ip")


def test_error_message_has_no_escapes():
    with pytest.raises(InvalidIPError) as excinfo:
        parse_ip(C1_PREFIX + "bogus-ip" + RLM)
    message = _friendly_error(excinfo.value)
    assert message == (
        "[ERROR] Invalid IP address.\n"
        "[!] Please enter a valid public IPv4 or IPv6 address."
    )
    assert "\\x" not in message


def test_clean_ip_text_edges_only():
    assert clean_ip_text(None) == ""
    assert clean_ip_text("   ") == ""
    with pytest.raises(InvalidIPError):
        clean_ip_text(12345)
