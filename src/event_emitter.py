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
    """

    def __init__(self) -> None:
        """Initialize empty event emitter."""
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable) -> None:
        """Remove a callback for an event."""
        if event in self._listeners:
            self._listeners[event].remove(callback)

    def emit(self, event: str, *args) -> None:
        """Emit an event, calling all registered callbacks with provided args."""
        for callback in self._listeners.get(event, []):
            callback(*args)

    def clear(self, event: str | None = None) -> None:
        """Clear listeners for a specific event, or all events if None."""
        if event is None:
            self._listeners.clear()
        elif event in self._listeners:
            del self._listeners[event]
