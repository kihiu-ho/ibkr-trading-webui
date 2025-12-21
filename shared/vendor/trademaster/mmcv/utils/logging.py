"""Minimal print_log helper for TradeMaster imports."""

from __future__ import annotations

from typing import Any, Optional


def print_log(msg: Any, logger: Optional[Any] = None, level: str = "INFO") -> None:
    """Print a log message (tiny subset of mmcv.utils.print_log)."""

    if logger is None:
        print(f"[{level}] {msg}")
        return

    log_fn = getattr(logger, str(level).lower(), None)
    if callable(log_fn):
        log_fn(msg)
        return
    try:
        logger.info(msg)
    except Exception:
        print(f"[{level}] {msg}")

