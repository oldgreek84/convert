from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class Signal:
    """Observer pattern implementation for event handling and notifications.

    This class provides a simple observer pattern mechanism that allows
    multiple handlers to be registered for specific events. When an event
    occurs, all registered handlers are called with the event data.

    Features:
        - Multiple handler registration
        - Event emission with arguments
        - Handler connection and disconnection
        - Type-safe callback management

    The signal pattern is commonly used for:
        - Error handling and reporting
        - Status updates and notifications
        - Event-driven architecture
        - Decoupled communication between components

    Attributes:
        handlers: List of registered callback functions

    Example:
        >>> signal = Signal()
        >>> signal.connect(lambda msg: print(f"Event: {msg}"))
        >>> signal.connect(logger.info)
        >>> signal.emit("Something happened")  # Calls all handlers
    """

    def __init__(self) -> None:
        """Initialize an empty signal with no handlers."""
        self.handlers: list[Callable] = []

    def emit(self, *args, **kwargs) -> None:
        """Emit the signal, calling all registered handlers.

        Args:
            *args: Positional arguments to pass to handlers
            **kwargs: Keyword arguments to pass to handlers
        """
        for handler in self.handlers:
            handler(*args, **kwargs)

    def connect(self, handler: Callable) -> None:
        """Register a new handler for this signal.

        Args:
            handler: Callable to be invoked when signal is emitted
        """
        self.handlers.append(handler)

    def disconnect(self, handler: Callable) -> None:
        """Remove a handler from this signal.

        Args:
            handler: Previously registered handler to remove
        """
        self.handlers.remove(handler)
