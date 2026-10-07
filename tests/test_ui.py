"""UI regression tests: ASCII-first, numbered menu, no giant boxes.

All assertions run against plain (color-disabled) output unless stated.
"""

from ipghost import formatting as fmt
from ipghost.models import Geolocation, IPInfo, NetworkInfo

PLAIN = fmt.Palette(enabled=False)


def _sample() -> IPInfo:
    return IPInfo(
        ip="35.94.45.221",
        ip_version=4,
        geolocation=Geolocation(
            country="United States",
            country_code="US",
            region="Oregon",
            city="Boardman",
            latitude=45.8398578,
            longitude=-119.7005791,
            timezone="America/Los_Angeles",
        ),
        network=NetworkInfo(isp="Example ISP", asn="AS12345"),
        google_maps_url="https://www.google.com/maps?q=45.8398578,-119.7005791",
    )


def test_banner_is_ascii_and_narrow():
    text = fmt.ascii_banner(PLAIN)
    assert text.isascii()
    assert "GLOBAL IP INTELLIGENCE" in text
    assert max(len(line) for line in text.splitlines()) <= 80
    for ch in ("╔", "═", "║", "╚", "╝", "✓", "→"):
        assert ch not in text


def test_no_giant_boxes_anywhere():
    combined = "\n".join(
        [
            fmt.startup(PLAIN, "0.1.0"),
            fmt.format_report(_sample(), PLAIN),
            fmt.interactive_menu(PLAIN, True),
            fmt.batch_header(PLAIN, 3),
            fmt.batch_summary(PLAIN, 3, 0),
        ]
    )
    for ch in ("╔", "═", "║", "╚", "╝"):
        assert ch not in combined


def test_no_ansi_when_disabled():
    combined = "\n".join(
        [
            fmt.startup(PLAIN, "0.1.0"),
            fmt.format_report(_sample(), PLAIN),
            fmt.interactive_menu(PLAIN, True),
        ]
    )
    assert "\x1b" not in combined


def test_menu_numbering_and_sections():
    menu = fmt.interactive_menu(PLAIN, True)
    for token in ("[01]", "[02]", "[03]", "[04]", "[00]", "[?]", "[::]"):
        assert token in menu
    report = fmt.format_report(_sample(), PLAIN)
    for section in (
        "[+] IP INFORMATION",
        "[+] GEOLOCATION",
        "[+] NETWORK",
        "[+] GOOGLE MAPS",
    ):
        assert section in report
    assert "Type" in report and "Public" in report
    assert "https://www.google.com/maps?q=45.8398578,-119.7005791" in report


def test_batch_style_and_summary_contract():
    assert "[::]" in fmt.batch_header(PLAIN, 5)
    assert fmt.batch_item(PLAIN, 1) == "[01]"
    summary = fmt.batch_summary(PLAIN, 3, 0)
    assert "Completed: 3" in summary
    assert "Failed: 0" in summary


def test_progress_stages_are_known():
    assert "Validating" in (fmt.stage_line(PLAIN, "validating") or "")
    assert "Querying" in (fmt.stage_line(PLAIN, "querying") or "")
    assert "cached" in (fmt.stage_line(PLAIN, "cached") or "").lower()
    assert "completed" in (fmt.stage_line(PLAIN, "done") or "").lower()
    assert fmt.stage_line(PLAIN, "bogus-stage") is None


def test_colors_present_when_enabled():
    vivid = fmt.Palette(enabled=True)
    assert "\x1b[" in fmt.ascii_banner(vivid)
    assert "\x1b[" in fmt.format_report(_sample(), vivid)
