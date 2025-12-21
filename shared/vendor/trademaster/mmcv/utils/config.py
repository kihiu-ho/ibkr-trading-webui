"""Minimal Config/ConfigDict to satisfy TradeMaster imports.

TradeMaster uses `mmcv.Config`/`mmcv.ConfigDict` primarily for type checks and
basic nested-dict access when reading/updating configs.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, MutableMapping, Optional, Tuple


class ConfigDict(dict):
    """A dict that also supports attribute access (very small subset)."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class Config:
    """A minimal config wrapper compatible with TradeMaster's expectations."""

    def __init__(self, cfg_dict: Optional[Dict[str, Any]] = None, *, filename: Optional[str] = None):
        object.__setattr__(self, "_cfg_dict", ConfigDict(cfg_dict or {}))
        object.__setattr__(self, "filename", filename)

    @property
    def _cfg_dict(self) -> ConfigDict:  # noqa: D401 - match upstream name
        return object.__getattribute__(self, "_cfg_dict")

    def __getitem__(self, key: str) -> Any:
        return self._cfg_dict[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._cfg_dict[key] = value

    def __contains__(self, key: object) -> bool:
        return key in self._cfg_dict

    def __iter__(self) -> Iterator[str]:
        return iter(self._cfg_dict)

    def __len__(self) -> int:
        return len(self._cfg_dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self._cfg_dict.get(key, default)

    def pop(self, key: str, default: Any = None) -> Any:
        return self._cfg_dict.pop(key, default)

    def items(self) -> Iterable[Tuple[str, Any]]:
        return self._cfg_dict.items()

    def __getattr__(self, name: str) -> Any:
        try:
            return self._cfg_dict[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_cfg_dict", "filename"}:
            object.__setattr__(self, name, value)
            return
        self._cfg_dict[name] = value

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Config(keys={list(self._cfg_dict.keys())}, filename={self.filename!r})"

