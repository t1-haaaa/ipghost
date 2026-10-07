"""Command-line interface — argparse front-end over the provider seam."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __app_name__, __version__
from . import cache as cache_mod
from . import formatting as fmt
from .config import Config
from .errors import (
    AuthError,
    BadResponseError,
    InvalidIPError,
    IpghostError,
    NetworkError,
    NonPublicIPError,
    NotFoundError,
    ProviderError,
    RateLimitError,
    TimeoutError,
    UsageError,
)
from .maps import build_maps_url, open_in_browser
from .models import IPInfo
from .providers.primary import IPWhoIsProvider
from .validators import ensure_public

EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USAGE = 2
EXIT_INVALID_IP = 3
EXIT_PROVIDER = 4
EXIT_CONFIG = 5


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ipghost.sh",
        description=(
            "IPGHOST — Global IP Intelligence & Geolocation CLI. "
            "Approximate IP-based geolocation only; not exact tracking."
        ),
        epilog=(
            "Examples:\n"
            "  ./ipghost.sh\n"
            "  ./ipghost.sh 8.8.8.8\n"
            "  ./ipghost.sh --json 8.8.8.8\n"
            "  ./ipghost.sh --map 8.8.8.8\n"
            "  ./ipghost.sh --file ips.txt\n"
            "  cat ips.txt | ./ipghost.sh --stdin\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("ip", nargs="?", help="Public IPv4/IPv6 address to look up.")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output.")
    parser.add_argument("--file", metavar="PATH", help="Batch lookup, one IP per line.")
    parser.add_argument("--stdin", action="store_true", help="Read IPs from STDIN.")
    parser.add_argument("--map", action="store_true", help="Print Google Maps URL and exit.")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors.")
    parser.add_argument("--debug", action="store_true", help="Verbose technical details.")
    parser.add_argument(
        "--timeout", type=float, default=None, help="Provider timeout in seconds."
    )
    parser.add_argument("-v", "--version", action="store_true", help="Show version.")
    return parser


def _provider(config: Config) -> IPWhoIsProvider:
    return IPWhoIsProvider(timeout=config.timeout, debug=config.debug)


def lookup_ip(ip_text: str, config: Config) -> IPInfo:
    validated = ensure_public(ip_text)
    cached = cache_mod.get(validated.text, config.cache_ttl)
    if cached is not None:
        try:
            return _info_from_dict(validated.text, cached)
        except Exception:
            pass
    info = _provider(config).lookup(validated.text)
    try:
        cache_mod.put(validated.text, info.to_dict(), config.cache_ttl)
    except Exception:
        pass
    return info


def _info_from_dict(ip_text: str, data: dict) -> IPInfo:
    from .models import Geolocation, NetworkInfo

    geo = data.get("geolocation", {}) if isinstance(data, dict) else {}
    net = data.get("network", {}) if isinstance(data, dict) else {}
    return IPInfo(
        ip=data.get("ip", ip_text),
        ip_version=int(data.get("ip_version", 4) or 4),
        geolocation=Geolocation(
            country=geo.get("country"),
            country_code=geo.get("country_code"),
            region=geo.get("region"),
            region_code=geo.get("region_code"),
            city=geo.get("city"),
            postal_code=geo.get("postal_code"),
            latitude=geo.get("latitude"),
            longitude=geo.get("longitude"),
            timezone=geo.get("timezone"),
        ),
        network=NetworkInfo(
            isp=net.get("isp"),
            organization=net.get("organization"),
            asn=net.get("asn"),
            as_name=net.get("as_name"),
            hostname=net.get("hostname"),
        ),
        google_maps_url=data.get("google_maps_url"),
    )


def _safe_filename(ip_text: str, ext: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", ip_text.strip())
    # IPv6 colons become underscores — safe on every filesystem.
    safe = safe.replace(":", "_")[:64] or "report"
    if safe in (".", "..", ""):
        safe = "report"
    return f"{safe}{ext}"


def _friendly_error(exc: BaseException) -> str:
    if isinstance(exc, NonPublicIPError):
        return f"[!] This is not a public routable IP.\n    {exc.message}"
    if isinstance(exc, InvalidIPError):
        return f"[ERROR] {exc.message}"
    if isinstance(exc, RateLimitError):
        return "[!] API rate limit reached.\n    Please wait and try again later."
    if isinstance(exc, TimeoutError):
        return "[ERROR] Provider request timed out."
    if isinstance(exc, AuthError):
        return f"[ERROR] {exc.message}"
    if isinstance(exc, NotFoundError):
        return f"[ERROR] {exc.message}"
    if isinstance(exc, (NetworkError, BadResponseError, ProviderError)):
        return f"[ERROR] {exc.message}"
    if isinstance(exc, IpghostError):
        return f"[ERROR] {exc.message}"
    return "[ERROR] Unexpected error occurred."


def _exit_for(exc: BaseException) -> int:
    if isinstance(exc, UsageError):
        return EXIT_USAGE
    if isinstance(exc, (InvalidIPError, NonPublicIPError)):
        return EXIT_INVALID_IP
    if isinstance(exc, IpghostError):
        return exc.exit_code
    if isinstance(exc, (ProviderError,)):
        return EXIT_PROVIDER
    return EXIT_GENERAL


def _print_json(info: IPInfo) -> None:
    # Pure JSON on stdout — no decorations, no colors.
    sys.stdout.write(json.dumps(info.to_dict(), indent=2, ensure_ascii=False) + "\n")


def _run_single(
    ip_text: str, config: Config, p: fmt.Palette, as_json: bool
) -> int:
    try:
        info = lookup_ip(ip_text, config)
    except BaseException as exc:  # noqa: BLE001 — mapped to friendly message
        if config.debug:
            import traceback

            traceback.print_exc()
        sys.stderr.write(_friendly_error(exc) + "\n")
        if isinstance(exc, (InvalidIPError, NonPublicIPError)):
            return EXIT_INVALID_IP
        if isinstance(exc, IpghostError):
            return exc.exit_code
        return EXIT_PROVIDER
    if as_json:
        _print_json(info)
    else:
        sys.stdout.write(fmt.format_report(info, p) + "\n")
    return EXIT_OK


def _run_map(ip_text: str, config: Config) -> int:
    try:
        info = lookup_ip(ip_text, config)
    except BaseException as exc:  # noqa: BLE001
        if config.debug:
            import traceback

            traceback.print_exc()
        sys.stderr.write(_friendly_error(exc) + "\n")
        return _exit_for(exc)
    url = info.google_maps_url or build_maps_url(
        info.geolocation.latitude, info.geolocation.longitude
    )
    if not url:
        sys.stdout.write("[!] Google Maps location unavailable.\n")
        return EXIT_OK
    sys.stdout.write("[+] GOOGLE MAPS\n\n    " + url + "\n")
    return EXIT_OK


def _read_lines_from_file(path_text: str) -> list[str]:
    path = Path(path_text)
    if not path.is_file():
        raise UsageError(f"File not found: {path_text}")
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise UsageError(f"Cannot read file: {path_text}") from exc
    return content.splitlines()


def _run_batch(items: Sequence[str], config: Config, p: fmt.Palette) -> int:
    # Deduplicate display but keep order; count blank/invalid without stopping.
    seen: set[str] = set()
    unique: list[str] = []
    for raw in items:
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if text.lower() not in seen:
            seen.add(text.lower())
            unique.append(text)
    total = len(unique)
    if total == 0:
        sys.stderr.write("[ERROR] No IP addresses found in input.\n")
        return EXIT_USAGE
    ok = 0
    failed = 0
    for index, candidate in enumerate(unique, start=1):
        sys.stdout.write(f"[{index}/{total}] {candidate}\n")
        try:
            info = lookup_ip(candidate, config)
        except RateLimitError:
            sys.stdout.write("[!] API rate limit reached.\n")
            sys.stdout.write("    Please wait and try again later.\n\n")
            failed += 1
            continue
        except (InvalidIPError, NonPublicIPError) as exc:
            sys.stdout.write(f"[!] {exc.message}\n\n")
            failed += 1
            continue
        except IpghostError as exc:
            sys.stdout.write(f"[ERROR] {exc.message}\n\n")
            failed += 1
            continue
        except Exception:  # noqa: BLE001 — batch must never stop on one IP
            sys.stdout.write("[ERROR] Unexpected error for this IP.\n\n")
            failed += 1
            continue
        sys.stdout.write(fmt.format_report(info, p) + "\n")
        ok += 1
    sys.stdout.write(f"Completed: {ok}\nFailed: {failed}\n")
    return EXIT_OK if failed == 0 else EXIT_GENERAL


def _export_json(info: IPInfo, config: Config) -> Path:
    out_dir = config.project_root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / _safe_filename(info.ip, ".json")
    # Resolve without following user input outside out_dir (no traversal).
    resolved = (out_dir / path.name).resolve()
    if out_dir.resolve() not in resolved.parents and resolved != out_dir.resolve():
        raise UsageError("Unsafe output filename.")
    resolved.write_text(
        json.dumps(info.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return resolved


def _save_report(info: IPInfo, config: Config, p: fmt.Palette) -> Path:
    plain = fmt.Palette(enabled=False)
    out_dir = config.project_root / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / _safe_filename(info.ip, ".txt")
    resolved = (out_dir / path.name).resolve()
    if out_dir.resolve() not in resolved.parents and resolved != out_dir.resolve():
        raise UsageError("Unsafe report filename.")
    resolved.write_text(fmt.format_report(info, plain) + "\n", encoding="utf-8")
    return resolved


def _interactive(config: Config, p: fmt.Palette) -> int:
    sys.stdout.write(fmt.banner(p) + "\n\n")
    current: IPInfo | None = None
    while True:
        try:
            raw = input("[?] Enter public IP address:\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.stdout.write("\nBye.\n")
            return EXIT_OK
        if not raw:
            sys.stderr.write("[ERROR] Empty IP address.\n")
            continue
        try:
            current = lookup_ip(raw, config)
        except BaseException as exc:  # noqa: BLE001
            if config.debug:
                import traceback

                traceback.print_exc()
            sys.stderr.write(_friendly_error(exc) + "\n")
            continue
        sys.stdout.write(fmt.format_report(current, p) + "\n")
        # Post-lookup menu.
        while True:
            maps_ok = bool(
                current.google_maps_url
                or build_maps_url(
                    current.geolocation.latitude, current.geolocation.longitude
                )
            )
            sys.stdout.write(fmt.interactive_menu(p, maps_ok))
            try:
                choice = input().strip()
            except (EOFError, KeyboardInterrupt):
                sys.stdout.write("\nBye.\n")
                return EXIT_OK
            if choice == "1":
                break  # another IP
            if choice == "2":
                url = current.google_maps_url or build_maps_url(
                    current.geolocation.latitude, current.geolocation.longitude
                )
                if not url:
                    sys.stdout.write("[!] Google Maps unavailable for this result.\n")
                    continue
                sys.stdout.write("[+] GOOGLE MAPS\n\n    " + url + "\n")
                opened, message = open_in_browser(url)
                if opened:
                    sys.stdout.write("[+] Opened in browser.\n")
                else:
                    sys.stdout.write(f"[!] {message}\n")
                    sys.stdout.write("[+] Google Maps:\n    " + url + "\n")
                continue
            if choice == "3":
                try:
                    path = _export_json(current, config)
                except IpghostError as exc:
                    sys.stderr.write(_friendly_error(exc) + "\n")
                    continue
                sys.stdout.write(f"[+] JSON exported to {path}\n")
                continue
            if choice == "4":
                try:
                    path = _save_report(current, config, p)
                except IpghostError as exc:
                    sys.stderr.write(_friendly_error(exc) + "\n")
                    continue
                sys.stdout.write(f"[+] Report saved to {path}\n")
                continue
            if choice == "0":
                sys.stdout.write("Bye.\n")
                return EXIT_OK
            sys.stdout.write("[?] Unknown option. Choose 1/2/3/4/0.\n")


def main(argv: Sequence[str] | None = None) -> int:
    # UTF-8 safe on Windows consoles (Linux is UTF-8 already).
    for stream in (sys.stdout, sys.stderr):
        reconfig = getattr(stream, "reconfigure", None)
        if callable(reconfig):
            try:
                reconfig(encoding="utf-8", errors="replace")
            except Exception:
                pass
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.version:
        sys.stdout.write(f"{__app_name__} {__version__}\n")
        return EXIT_OK

    # Project root = parent of src/… resolved from this file, overridable.
    project_root = Path(__file__).resolve().parents[2]
    config = Config.load(project_root)
    if args.timeout is not None:
        try:
            config.timeout = min(max(float(args.timeout), 1.0), 60.0)
        except (TypeError, ValueError):
            sys.stderr.write("[ERROR] Invalid --timeout value.\n")
            return EXIT_USAGE
    if args.debug:
        config.debug = True
    no_color = bool(args.no_color) or config.no_color
    palette = fmt.Palette(enabled=fmt.colors_enabled(no_color))

    if args.stdin:
        data = sys.stdin.read()
        return _run_batch(data.splitlines(), config, palette)
    if args.file:
        try:
            lines = _read_lines_from_file(args.file)
        except IpghostError as exc:
            sys.stderr.write(_friendly_error(exc) + "\n")
            return exc.exit_code
        return _run_batch(lines, config, palette)
    if args.map:
        if not args.ip:
            sys.stderr.write("[ERROR] --map requires an IP address.\n")
            return EXIT_USAGE
        return _run_map(args.ip, config)
    if args.ip:
        return _run_single(args.ip, config, palette, bool(args.json))
    # No IP + no mode => interactive, unless stdin is not a TTY with --json?
    if args.json:
        sys.stderr.write("[ERROR] --json requires an IP address.\n")
        return EXIT_USAGE
    return _interactive(config, palette)


if __name__ == "__main__":
    raise SystemExit(main())
