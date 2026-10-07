# Contributing to IPGHOST

## Development setup

```bash
git clone https://github.com/t1-haaaa/ipghost.git
cd ipghost
chmod +x ipghost.sh
python3 -m venv .venv
source .venv/bin/activate
pip install pytest ruff mypy
PYTHONPATH=src pytest -q
```

Kali / Debian notes: `python3`, `pip`, and `git` are enough. No root needed.

## Coding standards

- Python 3.9+, type hints, small modules, no duplicated logic.
- Zero runtime dependencies (stdlib only) unless justified in the PR.
- Never `except: pass` — map errors to `src/ipghost/errors.py`.
- No secrets in code, tests, docs, or logs.
- Shell: `bash`, `set -euo pipefail`, ShellCheck-clean.

## Testing

```bash
PYTHONPATH=src pytest -q
python -m ruff check src tests
python -m mypy src
./ipghost.sh --help
./ipghost.sh --version
```

Unit tests must use mocks — no real API calls in `pytest`.

## Pull requests

- One topic per PR, clear title (`feat:`, `fix:`, `docs:` …).
- Update `CHANGELOG.md` under `Unreleased`.
- Update `README.md` only for features that actually exist.
- Confirm `git status` shows no `.env`, `.venv/`, reports, or secrets.

## Issue reporting

Include OS, Python version, exact command, expected vs actual output.
Redact IPs only if they are sensitive; otherwise real examples help.
