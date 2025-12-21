"""Minimal Registry to satisfy TradeMaster's builder modules."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class Registry:
    """A tiny subset of mmcv.utils.Registry used by TradeMaster."""

    def __init__(self, name: str):
        self._name = str(name)
        self._module_dict: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return self._name

    def get(self, key: str) -> Optional[Any]:
        return self._module_dict.get(key)

    def register_module(self, name: Optional[str] = None) -> Callable[[Type[T]], Type[T]]:
        def _register(cls: Type[T]) -> Type[T]:
            module_name = str(name or cls.__name__)
            self._module_dict[module_name] = cls
            return cls

        return _register

