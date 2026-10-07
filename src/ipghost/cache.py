"""Tiny file cache. Stores provider-normalized dicts only — never secrets."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def cache_dir() -> Path:
    import os

    base = os.environ.get("XDG_CACHE_HOME", "")
    if base:
        root = Path(base) / "ipghost"
    else:
        root = Path.home() / ".cache" / "ipghost"
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return root


def _path_for(ip: str) -> Path:
    digest = hashlib.sha256(ip.strip().lower().encode()).hexdigest()[:32]
    return cache_dir() / f"{digest}.json"


def get(ip: str, ttl: int) -> dict[str, Any] | None:
    if ttl <= 0:
        return None
    path = _path_for(ip)
    try:
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        saved = float(payload.get("_saved_at", 0))
        if time.time() - saved > ttl:
            return None
        data = payload.get("data")
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def put(ip: str, data: dict[str, Any], ttl: int) -> None:
    if ttl <= 0:
        return
    # Refuse to cache anything that looks like it contains a secret.
    lowered = json.dumps(data).lower()
    if "api_key" in lowered or "apikey" in lowered:
        return
    path = _path_for(ip)
    try:
        path.write_text(
            json.dumps({"_saved_at": time.time(), "data": data}),
            encoding="utf-8",
        )
    except OSError:
        return
