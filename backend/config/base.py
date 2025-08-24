"""
Shim for backend.config.base that proxies to top-level config.base if available.
"""

try:
    from config.base import Config as _RootConfig  # type: ignore
    Config = _RootConfig
except Exception:
    class Config:  # Minimal fallback used in tests
        pass

__all__ = ["Config"]






