# IPGHOST — Global IP Intelligence & Geolocation CLI

Terminal-only, Linux-first tool that takes a **public** IPv4/IPv6 address and
returns GeoIP + network intelligence from a trusted provider, with validated
Google Maps links, machine-readable JSON, and batch/STDIN modes.

> [!IMPORTANT]
> IP geolocation is **approximate**. It does not identify an exact physical
> address, person, or real-time device location. IPGHOST is for network
> administration, troubleshooting, security research, OSINT, and education.

## Features

- Interactive menu + direct lookup + `--json` + `--file` + `--stdin` + `--map`
- Public-IP-only validation (private/loopback/link-local/multicast/reserved rejected with reasons)
- IPv4 + IPv6 (`ipaddress` stdlib, no regex hacks)
- Provider abstraction (`providers/base.py` → `providers/primary.py`, normalized `IPInfo` model)
- Google Maps URL from validated coordinates (`-90..90`, `-180..180`), safe `xdg-open`
- Clean terminal report, `--no-color` / `NO_COLOR` friendly
- JSON contract for scripting, batch summaries, report/JSON export
- Timeout + limited retry (5xx only), HTTP 429/401/403/404 handling, no tracebacks by default
- Local file cache with TTL (`IPGHOST_CACHE_TTL`, `0` disables)
- Zero runtime dependencies (Python stdlib only), no root, works from any cwd

## Requirements

- Linux (Kali, Ubuntu/Debian-like), Bash, `python3` 3.9+
- Internet (HTTPS to `ipwho.is`)
- Optional: `xdg-open` for one-key browser opening
- Dev: `pytest`, `ruff`, `mypy`, `shellcheck`

## Installation

```bash
git clone https://github.com/t1-haaaa/ipghost.git
cd ipghost
chmod +x ipghost.sh
./ipghost.sh
```

First run creates `.venv/` automatically (no sudo). No global install needed.

## Usage

### Interactive Mode

```bash
./ipghost.sh
```

```
╔══════════════════════════════════════════════════════════╗
║                         IPGHOST                          ║
║             GLOBAL IP INTELLIGENCE CLI                   ║
╚══════════════════════════════════════════════════════════╝

[?] Enter public IP address:
> 8.8.8.8
```

After a lookup:

```
[1] Analyze another IP
[2] Open location in Google Maps
[3] Export JSON
[4] Save report
[0] Exit
```

### Direct Lookup

```bash
./ipghost.sh 8.8.8.8
```

### JSON Mode

```bash
./ipghost.sh --json 8.8.8.8
```

```json
{
  "ip": "8.8.8.8",
  "ip_version": 4,
  "geolocation": {
    "country": "United States",
    "country_code": "US",
    "region": "California",
    "city": "Mountain View",
    "postal_code": "94043",
    "latitude": 37.386,
    "longitude": -122.0838,
    "timezone": "America/Los_Angeles"
  },
  "network": {
    "isp": "Google LLC",
    "organization": "Google LLC",
    "asn": "AS15169",
    "hostname": null
  },
  "google_maps_url": "https://www.google.com/maps?q=37.386,-122.0838"
}
```

### Batch Mode

```bash
./ipghost.sh --file ips.txt
```

```
[1/3] 8.8.8.8
[+] Success …

Completed: 2
Failed: 1
```

Blank lines, `#` comments, duplicates, invalid IPs, and per-IP API errors are
handled without stopping the batch.

### STDIN Mode

```bash
cat ips.txt | ./ipghost.sh --stdin
echo "8.8.8.8" | ./ipghost.sh --stdin
```

### Google Maps

```bash
./ipghost.sh --map 8.8.8.8
```

```
[+] GOOGLE MAPS

    https://www.google.com/maps?q=37.386,-122.0838
```

The browser never opens automatically on lookup — only from menu option `2`.

### Help / Version

```bash
./ipghost.sh --help
./ipghost.sh --version
./ipghost.sh --debug 8.8.8.8
./ipghost.sh --no-color 8.8.8.8
./ipghost.sh --timeout 15 8.8.8.8
```

## Configuration

| Variable            | Default | Meaning                              |
| ------------------- | ------- | ------------------------------------ |
| `IPGHOST_API_KEY`   | empty   | Reserved (default provider needs none)|
| `IPGHOST_TIMEOUT`   | `10`    | Seconds, clamped 1–60                |
| `IPGHOST_CACHE_TTL` | `3600`  | Seconds, `0` disables cache          |
| `IPGHOST_NO_COLOR`  | empty   | `1` disables colors                  |
| `IPGHOST_DEBUG`     | empty   | `1` shows tracebacks (no secrets)    |

```bash
cp .env.example .env
```

`.env` is git-ignored. See `docs/configuration.md`.

## Providers

Primary: **ipwho.is** — `GET https://ipwho.is/{ip}`, free, HTTPS, no key,
IPv4+IPv6. Adding another provider = new `GeoIPProvider` adapter + mocked
tests; CLI/formatters/maps stay untouched. See `docs/providers.md` and
`docs/architecture.md`.

## Examples

```bash
./ipghost.sh 1.1.1.1
./ipghost.sh --json 2001:4860:4860::8888
./ipghost.sh --map 8.8.8.8
printf '8.8.8.8\n1.1.1.1\n' | ./ipghost.sh --stdin
```

Private input is refused before any network call:

```
[!] This is not a public routable IP.
    192.168.1.1 is not a public routable IP (private address).
```

## Security

- No secrets in code/README/tests/CI; `.env` never tracked.
- HTTPS only, timeouts everywhere, limited retry, 429 respected.
- `subprocess` with argument lists (no `shell=True`, no `os.system`).
- Maps URL built from validated floats only; filenames sanitized (no traversal).
- Untrusted provider JSON is type-checked field by field.
- See `SECURITY.md`.

## Limitations

- Geolocation is city/region-level approximation from the provider.
- Some IPs (notably IPv6 or anycast) may return sparse fields → `N/A` / `null`.
- Free provider quotas apply; on 429 wait and retry.
- Browser opening needs `xdg-open` (or fallback); the URL is always printed.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest ruff mypy
PYTHONPATH=src pytest -q
python -m ruff check src tests
python -m mypy src
```

Project layout and seams: `docs/architecture.md`.

## Testing

```bash
PYTHONPATH=src pytest -q
```

Mocked unit tests only — no live API in `pytest`. Manual live checks:

```bash
./ipghost.sh --help
./ipghost.sh --version
./ipghost.sh 8.8.8.8
./ipghost.sh --json 8.8.8.8
./ipghost.sh --map 8.8.8.8
```

## Contributing

See `CONTRIBUTING.md` and `CODE_OF_CONDUCT.md`.

## License

MIT — see `LICENSE`.
