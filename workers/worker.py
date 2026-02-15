import queue
import threading
import time
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any

import requests

from src.event_emitter import EventEmitter
from utils.common_utils import coroutine

_DEFAULT_POOL = ThreadPoolExecutor()


def threadpool(func, executor=None):
    """Decorator for submitting functions to a thread pool executor.

    This decorator automatically submits the decorated function to a thread
    pool for concurrent execution, useful for I/O-bound or long-running operations.

    Args:
        func: Function to be executed in the thread pool
        executor: Optional ThreadPoolExecutor instance (uses default if None)

    Returns:
        Decorated function that returns a Future object
    """

    @wraps(func)
    def wrap(*args, **kwargs):
        return (executor or _DEFAULT_POOL).submit(func, *args, **kwargs)

    return wrap


def threaded(func, daemon=False):
    """Decorator for executing functions in separate threads with result queuing.

    This decorator runs the decorated function in a new thread and provides
    a queue-based mechanism for retrieving results. Useful for long-running
    operations that need to run concurrently with the main thread.

    Args:
        func: Function to be executed in a separate thread
        daemon: Whether the created thread should be a daemon thread

    Returns:
        Decorated function that returns a Thread object with attached result queue
    """

    def wrapped_f(wrapped_q, *args, **kwargs):
        """Execute the function and put the result in the queue.

        Args:
            wrapped_q: Queue to store the function result
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        """
        ret = func(*args, **kwargs)
        wrapped_q.put(ret)

    def wrap(*args, **kwargs):
        """Create and start a new thread for function execution.

        Returns:
            Thread object with result_queue attribute attached
        """
        queue_q = queue.Queue()

        thread = threading.Thread(target=wrapped_f, args=(queue_q, *args), kwargs=kwargs)
        thread.daemon = daemon
        thread.start()
        setattr(thread, "result_queue", queue_q)  # Dynamically attach result queue
        return thread

    return wrap


class ThreadError(Exception):
    """Exception raised when thread operations fail or are in invalid state."""


class ThreadWorker:
    """Threading-based worker implementation for concurrent task execution.

    This worker provides concurrent execution capabilities using Python's
    threading module. It allows conversion operations to run in the background
    while keeping the user interface responsive. The worker handles error
    propagation and result retrieval through an event-based mechanism.

    Features:
        - Background thread execution
        - Error handling with event emission
        - Result storage and retrieval
        - Completion status checking
        - Callback-based error handling

    The worker follows a simple lifecycle:
    1. execute() starts a function in a background thread
    2. is_completed() checks if execution finished
    3. get_result() retrieves the function's return value
    4. Error handlers are called automatically if exceptions occur

    Attributes:
        _thread: Background thread instance.
        _result: Stored result from function execution.
        events: EventEmitter for error handling and notifications.

    Example:
        >>> worker = ThreadWorker()
        >>> worker.set_error_handler(lambda e: print(f"Error: {e}"))
        >>> worker.execute(some_long_function, arg1, arg2)
        >>> while not worker.is_completed():
        ...     time.sleep(0.1)
        >>> result = worker.get_result()
    """

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._result = None
        self.events = EventEmitter()

    def is_completed(self) -> bool:
        if self._thread is None:
            raise ThreadError
        return not self._thread.is_alive()

    def get_result(self) -> Any:
        return self._result

    def set_error_handler(self, handler: Callable) -> None:
        self.events.on("error", handler)

    def execute(self, func: Callable, *args, **kwargs) -> None:
        self._thread = threading.Thread(target=self.wrapper, args=(func, *args), kwargs=kwargs)
        self._thread.start()

    def wrapper(self, func: Callable, *args, **kwargs) -> None:
        try:
            result = func(*args, **kwargs)
            self._result = result
        except Exception as ex:
            self.events.emit("error", ex)


class WorkerCoroutine:
    def is_completed(self):
        return self._status in ["error", "completed"]

    def execute(self):
        self.producer(self.get_status_cor())

    def producer(self, main_cor, until_done=False):
        while True:
            time.sleep(3)
            main_cor.send(True)

            if not until_done:
                break

            if self.is_completed():
                main_cor.close()
                break

    @coroutine
    def get_some_cor(self):
        while True:
            _, resp_status = self.get_response_status()
            _ = yield resp_status

    @coroutine
    def get_status_cor(self):
        try:
            while True:
                run = yield
                if run:
                    res, resp_status = self.job_process(self.args, self.kwargs)
                    yield res, resp_status
                    self._status = res.json()["message"]
        except GeneratorExit:
            print("closing.........")

    def test_worker(self):
        checker = self.checker()
        sum_cor = self.sum_cor(checker)
        self.next_producer(sum_cor)
        return sum_cor

    def next_producer(self, main_cor, waiter=None):
        try:
            main_cor.send(True)
        except StopIteration:
            print("closing....")

    @coroutine
    def sum_cor(self, checker):
        try:
            res = yield from checker
        except Exception as ex:
            print(f"{ex = }")

    def checker(self):
        resp_status = False
        while True:
            try:
                time.sleep(3)
                res, resp_status = self.get_response_status()
                print(f"{res = } {resp_status = }")
            except StopIteration:
                break
            else:
                self._status = resp_status
                if resp_status in ["completed", "error"]:
                    print("COMPLETED")
                    break
        return resp_status

    @coroutine
    def waiter_cor(self, main=None):
        try:
            while True:
                status = yield
                print(f"{type(status) = }")
                print(f"waiter: {status = }")
                if isinstance(status, Generator):
                    main = status
                self._status = status

                if status in ["completed", "error"]:
                    # checker.close()
                    if main is not None:
                        main.close()
                    return

                if main is not None:
                    main.send(True)

        except GeneratorExit:
            print("waiter coroutine closing...")

    @coroutine
    def check_cor(self, waiter):
        resp_status = "wait"
        try:
            while True:
                check = yield
                print(f"checker: {check = }")
                if check:
                    time.sleep(3)
                    _, resp_status = self.get_response_status()
                    # waiter_cor.send(resp_status)
                    # yield resp_status
                    waiter.send(resp_status)
        except GeneratorExit:
            print("check coroutine closing...")


if __name__ == "__main__":

    def get_response_status(some):
        res = requests.get("http://localhost:5000/", json={"some": some})
        return res, res.json()["status"]["code"]

    worker = ThreadWorker()
    worker.execute(get_response_status, 11)
