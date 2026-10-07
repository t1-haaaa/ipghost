"""Configuration from environment + optional local .env file.

No secrets live in source. The default provider needs NO key; IPGHOST_API_KEY
exists only for future providers that require one.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(project_root: Path) -> None:
    """Minimal .env loader (KEY=VALUE, ignores comments). No overrides."""
    env_file = project_root / ".env"
    if not env_file.is_file():
        return
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"' ")
            if key and key not in os.environ:
                os.environ[key] = value
    except OSError:
        return


@dataclass
class Config:
    api_key: str = ""
    timeout: float = 10.0
    cache_ttl: int = 3600
    no_color: bool = False
    debug: bool = False
    project_root: Path = Path(".")

    @classmethod
    def load(cls, project_root: Path | None = None) -> Config:
        root = Path(project_root) if project_root else Path.cwd()
        _load_dotenv(root)

        def _env(name: str, default: str = "") -> str:
            return os.environ.get(name, default).strip()

        try:
            timeout = float(_env("IPGHOST_TIMEOUT", "10") or "10")
        except ValueError:
            timeout = 10.0
        timeout = min(max(timeout, 1.0), 60.0)

        try:
            ttl = int(_env("IPGHOST_CACHE_TTL", "3600") or "3600")
        except ValueError:
            ttl = 3600
        ttl = max(ttl, 0)

        no_color = (
            _env("IPGHOST_NO_COLOR", "").lower() in ("1", "true", "yes")
            or _env("NO_COLOR", "") != ""
        )
        debug = _env("IPGHOST_DEBUG", "").lower() in ("1", "true", "yes")

        return cls(
            api_key=_env("IPGHOST_API_KEY", ""),
            timeout=timeout,
            cache_ttl=ttl,
            no_color=no_color,
            debug=debug,
            project_root=root,
        )
