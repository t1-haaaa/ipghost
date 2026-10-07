"""Minimal HTTPS JSON client on top of the stdlib.

Zero runtime dependencies by design. Limited retry only for transient
failures (network blips, HTTP 5xx). Never retries 401/403/404/429.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .errors import (
    AuthError,
    BadResponseError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)

_USER_AGENT = "IPGHOST/0.1.0 (+https://github.com/t1-haaaa/ipghost)"


def get_json(
    url: str,
    timeout: float = 10.0,
    debug: bool = False,
    _opener: Any | None = None,
) -> Any:
    if not url.startswith("https://"):
        raise NetworkError("Refusing non-HTTPS provider URL.")

    last_exc: Exception | None = None
    # 1 initial try + 2 retries for transient errors only.
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": _USER_AGENT}
            )
            opener = _opener or urllib.request.urlopen
            with opener(req, timeout=timeout) as resp:  # type: ignore[arg-type]
                status = getattr(resp, "status", 200) or 200
                raw = resp.read().decode("utf-8", errors="replace")
            if status == 429:
                raise RateLimitError(
                    "API rate limit reached. Please wait and try again later."
                )
            if status in (401, 403):
                raise AuthError(f"Provider authentication failed (HTTP {status}).")
            if status == 404:
                raise NotFoundError("Provider has no data for this IP (HTTP 404).")
            if 500 <= status <= 599:
                raise NetworkError(f"Provider unavailable (HTTP {status}).")
            try:
                return json.loads(raw) if raw else None
            except json.JSONDecodeError as exc:
                raise BadResponseError("Provider returned malformed JSON.") from exc
        except RateLimitError:
            raise
        except AuthError:
            raise
        except NotFoundError:
            raise
        except BadResponseError:
            raise
        except urllib.error.HTTPError as exc:
            code = exc.code
            if code == 429:
                raise RateLimitError(
                    "API rate limit reached. Please wait and try again later."
                ) from exc
            if code in (401, 403):
                raise AuthError(
                    f"Provider authentication failed (HTTP {code})."
                ) from exc
            if code == 404:
                raise NotFoundError(
                    "Provider has no data for this IP (HTTP 404)."
                ) from exc
            if 500 <= code <= 599:
                last_exc = NetworkError(f"Provider unavailable (HTTP {code}).")
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise last_exc from exc
            raise NetworkError(f"Provider request failed (HTTP {code}).") from exc
        except TimeoutError as exc:  # urllib maps timeouts to TimeoutError/URLError
            last_exc = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise TimeoutError("Provider request timed out.") from exc
        except urllib.error.URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            if "timed out" in reason.lower() or "timeout" in reason.lower():
                last_exc = exc
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise TimeoutError("Provider request timed out.") from exc
            last_exc = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise NetworkError(f"Network error: {reason}.") from exc
        except (ConnectionError, OSError) as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
                continue
            raise NetworkError(f"Network error: {exc}.") from exc
    raise NetworkError(f"Network error: {last_exc}.")
