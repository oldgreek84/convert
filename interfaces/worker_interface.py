from __future__ import annotations

from typing import Callable, Protocol, Any


class Worker(Protocol):
    """Allow to run processes concurrently"""

    def is_completed(self) -> bool:
        raise NotImplementedError

    def get_result(self) -> Any:
        raise NotImplementedError

    def execute(self, func: Callable, *args, **kwargs) -> None:
        raise NotImplementedError

    def set_error_handler(self, handler: Callable) -> None:
        raise NotImplementedError
