from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


# TODO: create decorator to add handlers
class Signal:
    """Provide observer pattern behavior"""

    def __init__(self) -> None:
        self.handlers: list[Callable] = []

    def emit(self, *args, **kwargs) -> None:
        for handler in self.handlers:
            handler(*args, **kwargs)

    def connect(self, handler: Callable) -> None:
        self.handlers.append(handler)

    def disconnect(self, handler: Callable) -> None:
        self.handlers.remove(handler)
