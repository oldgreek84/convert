"""Event Emitter for decoupled communication.

This module provides a simple event emitter for implementing the Observer
pattern. It allows objects to emit events without knowing who is listening,
enabling loose coupling between components.

The EventEmitter is used by Converter to emit progress events that
Application subscribes to and forwards to the View.

Example:
    >>> emitter = EventEmitter()
    >>> emitter.on('status', lambda s: print(f"Status: {s}"))
    >>> emitter.emit('status', 'processing')
    Status: processing
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class EventEmitter:
    """Simple event emitter implementing the Observer pattern.

    Allows registering callbacks for named events and emitting events
    with arbitrary arguments. Multiple listeners can be registered
    for the same event.

    Attributes:
        _listeners: Dictionary mapping event names to list of callbacks

    Example:
        >>> emitter = EventEmitter()
        >>>
        >>> # Register listeners
        >>> emitter.on('message', print)
        >>> emitter.on('message', logger.info)
        >>>
        >>> # Emit event - both listeners receive it
        >>> emitter.emit('message', 'Hello')
        Hello
    """

    def __init__(self) -> None:
        """Initialize empty event emitter."""
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event.

        Multiple callbacks can be registered for the same event.
        Callbacks are called in registration order.

        Args:
            event: Event name to listen for
            callback: Function to call when event is emitted
        """
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Remove a callback for an event.

        Args:
            event: Event name
            callback: Callback to remove

        Note:
            If callback is not found in the event listeners, this may raise
            ValueError from the underlying list.remove() call.
        """
        if event in self._listeners:
            self._listeners[event].remove(callback)

    def emit(self, event: str, *args) -> None:
        """Emit an event with arguments.

        Calls all registered callbacks for the event with provided args.
        If no callbacks are registered, does nothing.

        Args:
            event: Event name to emit
            *args: Arguments to pass to callbacks
        """
        for callback in self._listeners.get(event, []):
            callback(*args)

    def clear(self, event: str | None = None) -> None:
        """Clear listeners for an event or all events.

        Args:
            event: Event name to clear, or None to clear all
        """
        if event is None:
            self._listeners.clear()
        elif event in self._listeners:
            del self._listeners[event]
