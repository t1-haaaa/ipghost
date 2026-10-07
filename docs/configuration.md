# Configuration

| Variable           | Default | Purpose                                  |
| ------------------ | ------- | ---------------------------------------- |
| `IPGHOST_API_KEY`  | empty   | Reserved for future key-based providers. |
| `IPGHOST_TIMEOUT`  | `10`    | Provider timeout in seconds (1–60).      |
| `IPGHOST_CACHE_TTL`| `3600`  | Cache seconds; `0` disables.             |
| `IPGHOST_NO_COLOR` | empty   | `1` forces plain output.                 |
| `IPGHOST_DEBUG`    | empty   | `1` enables tracebacks (no secrets).     |
| `NO_COLOR`         | empty   | Standard opt-out, also respected.        |

Copy `.env.example` to `.env` for local tweaks. `.env` is git-ignored and
never overrides real environment variables.

CLI flags: `--no-color`, `--debug`, `--timeout SECS`.

## Input encoding

Surrounding whitespace and invisible edge characters (BOM, bidi marks,
stray terminal control bytes) are removed before validation; anything
unexpected inside the address is rejected with a clean message. `ipghost.sh`
defaults `PYTHONIOENCODING` to `utf-8` only when unset — `LANG`/`LC_ALL`
and any user-provided value are never overridden.
