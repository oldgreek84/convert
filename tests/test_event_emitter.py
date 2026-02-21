"""Unit tests for EventEmitter class."""

from __future__ import annotations

import unittest

from src.event_emitter import EventEmitter


class TestEventEmitter(unittest.TestCase):
    """Test cases for EventEmitter."""

    def setUp(self):
        self.emitter = EventEmitter()

    def test_on_and_emit(self):
        results = []
        self.emitter.on("test", results.append)
        self.emitter.emit("test", "hello")
        self.assertEqual(results, ["hello"])

    def test_emit_multiple_listeners(self):
        results_a = []
        results_b = []
        self.emitter.on("test", results_a.append)
        self.emitter.on("test", results_b.append)
        self.emitter.emit("test", "data")
        self.assertEqual(results_a, ["data"])
        self.assertEqual(results_b, ["data"])

    def test_emit_preserves_registration_order(self):
        order = []
        self.emitter.on("test", lambda _: order.append("first"))
        self.emitter.on("test", lambda _: order.append("second"))
        self.emitter.emit("test", None)
        self.assertEqual(order, ["first", "second"])

    def test_emit_unknown_event_does_nothing(self):
        self.emitter.emit("nonexistent", "data")  # should not raise

    def test_emit_passes_multiple_args(self):
        results = []
        self.emitter.on("test", lambda a, b: results.append((a, b)))
        self.emitter.emit("test", 1, 2)
        self.assertEqual(results, [(1, 2)])

    def test_off_removes_callback(self):
        results = []
        callback = results.append
        self.emitter.on("test", callback)
        self.emitter.off("test", callback)
        self.emitter.emit("test", "data")
        self.assertEqual(results, [])

    def test_off_nonexistent_event_does_nothing(self):
        self.emitter.off("nonexistent", lambda: None)  # should not raise

    def test_clear_specific_event(self):
        results = []
        self.emitter.on("a", results.append)
        self.emitter.on("b", results.append)
        self.emitter.clear("a")
        self.emitter.emit("a", "gone")
        self.emitter.emit("b", "still here")
        self.assertEqual(results, ["still here"])

    def test_clear_all_events(self):
        results = []
        self.emitter.on("a", results.append)
        self.emitter.on("b", results.append)
        self.emitter.clear()
        self.emitter.emit("a", "gone")
        self.emitter.emit("b", "also gone")
        self.assertEqual(results, [])

    def test_clear_nonexistent_event_does_nothing(self):
        self.emitter.clear("nonexistent")  # should not raise


if __name__ == "__main__":
    unittest.main()
