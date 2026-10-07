# Architecture

```
IP lookup
    ↓
Provider interface (src/ipghost/providers/base.py)
    ↓
Primary adapter: ipwho.is (src/ipghost/providers/primary.py)
    ↓
Normalized result: IPInfo (src/ipghost/models.py)
    ↓
CLI / JSON / Maps / batch / reports (src/ipghost/cli.py, formatting.py, maps.py)
```

Deep module: `providers/` hides all HTTP + provider field names behind
`GeoIPProvider.lookup(ip) -> IPInfo`. Callers and tests cross that one seam.

Other modules and their seams:

- `validators.py` — `ensure_public(raw) -> ValidatedIP` (stdlib `ipaddress`).
- `maps.py` — `build_maps_url(lat, lon) -> str | None`, `open_in_browser(url)`.
- `http.py` — `get_json(url, timeout)`, HTTPS-only, limited retry for 5xx only.
- `models.py` — `IPInfo.to_dict()` is the JSON contract.
- `cache.py` — file cache in `~/.cache/ipghost`, TTL via `IPGHOST_CACHE_TTL`.
- `config.py` — env + `.env` loader, never logs secrets.
- `formatting.py` — terminal report; colors decorative only.
- `cli.py` — argparse modes, exit codes, batch/stdin engines, export paths.
