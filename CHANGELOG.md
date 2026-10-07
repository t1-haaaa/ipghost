# Changelog

All notable changes to IPGHOST are documented here.
Format follows Keep a Changelog; versions follow SemVer.

## Unreleased

- fix: handle terminal input encoding safely — strip invisible edge
  characters (C1 controls, BOM, bidi marks) before IP validation, clean
  invalid-IP messages (no raw escape echo), default `PYTHONIOENCODING=utf-8`
  when unset, UTF-8 stdin handling.

## 0.1.0 — 2026-10-07

- Initial IPGHOST release: interactive / direct / `--json` / `--file` /
  `--stdin` / `--map` / `--help` / `--version`.
- Provider abstraction with `ipwho.is` primary (HTTPS, no key, IPv4+IPv6).
- Normalized `IPInfo` data model, coordinate validation, Google Maps URLs.
- Safe browser opening (`xdg-open`, no shell injection), report/JSON export.
- File cache with TTL, timeout/retry, rate-limit handling, exit codes.
- pytest suite (mocked), GitHub Actions CI, docs, MIT license.
