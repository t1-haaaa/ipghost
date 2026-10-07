"""Application-wide error types.

All user-facing messages are built from these — cli.py never shows
a raw traceback unless --debug is passed.
"""

from __future__ import annotations


class IpghostError(Exception):
    """Base class. Carries a machine-readable exit code."""

    exit_code: int = 1

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UsageError(IpghostError):
    exit_code = 2


class InvalidIPError(IpghostError):
    exit_code = 3


class NonPublicIPError(InvalidIPError):
    """A syntactically valid IP that is not a public routable address."""


class ProviderError(IpghostError):
    exit_code = 4


class NetworkError(ProviderError):
    pass


class TimeoutError_(ProviderError):
    pass


TimeoutError = TimeoutError_  # alias kept short in imports


class RateLimitError(ProviderError):
    pass


class AuthError(ProviderError):
    pass


class NotFoundError(ProviderError):
    pass


class BadResponseError(ProviderError):
    pass


class ConfigError(IpghostError):
    exit_code = 5
