"""Minimal MMCV compatibility layer for vendored TradeMaster.

TradeMaster upstream depends on small parts of MMCV (Registry, Config, print_log).
To keep this project buildable without pulling the full MMCV stack, we vendor a
tiny subset that satisfies TradeMaster imports used by our Airflow integration.

This is **not** a complete MMCV implementation.
"""

from __future__ import annotations

from .utils.config import Config, ConfigDict

__all__ = [
    "Config",
    "ConfigDict",
]

