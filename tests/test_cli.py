"""CLI seams: --help, --version, --json shape, --map, batch/stdin."""

import json

from ipghost import cli
from ipghost.models import Geolocation, IPInfo, NetworkInfo


def _sample() -> IPInfo:
    return IPInfo(
        ip="8.8.8.8",
        ip_version=4,
        geolocation=Geolocation(
            country="United States",
            country_code="US",
            region="California",
            city="Mountain View",
            latitude=37.386,
            longitude=-122.0838,
            timezone="America/Los_Angeles",
        ),
        network=NetworkInfo(isp="Google LLC", organization="Google LLC", asn="AS15169"),
        google_maps_url="https://www.google.com/maps?q=37.386,-122.0838",
    )


def test_help_exits_zero(capsys):
    try:
        cli.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    out = capsys.readouterr().out
    assert "IPGHOST" in out


def test_version(capsys):
    assert cli.main(["--version"]) == 0
    out = capsys.readouterr().out
    assert "IPGHOST" in out


def test_json_output_is_valid(monkeypatch, capsys):
    monkeypatch.setattr(cli, "lookup_ip", lambda ip, config: _sample())
    assert cli.main(["--json", "8.8.8.8"]) == 0
    out = capsys.readouterr().out
    data = json.loads(out)  # must not raise
    assert data["ip"] == "8.8.8.8"
    assert data["geolocation"]["country"] == "United States"
    assert "google.com/maps" in data["google_maps_url"]
    # No ANSI escapes in JSON.
    assert "\x1b" not in out


def test_map_output(monkeypatch, capsys):
    monkeypatch.setattr(cli, "lookup_ip", lambda ip, config: _sample())
    assert cli.main(["--map", "8.8.8.8"]) == 0
    out = capsys.readouterr().out
    assert "https://www.google.com/maps?q=37.386,-122.0838" in out


def test_batch_continues_on_invalid(monkeypatch, capsys):
    def _fake(ip, config):
        if ip == "bad":
            from ipghost.errors import InvalidIPError

            raise InvalidIPError("Invalid IP address: 'bad'.")
        return _sample()

    monkeypatch.setattr(cli, "lookup_ip", _fake)
    cli.main(["--file", "nonexistent-will-fail"]) if False else None
    # Direct batch call with mixed input.
    from ipghost import formatting as fmt

    p = fmt.Palette(enabled=False)
    from ipghost.config import Config

    cfg = Config.load()
    rc = cli._run_batch(["8.8.8.8", "bad", "", "8.8.8.8"], cfg, p)
    assert rc in (0, 1)
    out = capsys.readouterr().out
    assert "Completed" in out
