import queue
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Any, Protocol

import requests
from observer import Signal
from utils import coroutine

_DEFAULT_POOL = ThreadPoolExecutor()


def threadpool(func, executor=None):
    """decorator for long-time operation"""

    @wraps(func)
    def wrap(*args, **kwargs):
        return (executor or _DEFAULT_POOL).submit(func, *args, **kwargs)

    return wrap


def threaded(func, daemon=False):
    """decorator for long-time operation"""

    def wrapped_f(wrapped_q, *args, **kwargs):
        """this function calls the decorated function and puts the
        result in a queue
        """
        ret = func(*args, **kwargs)
        wrapped_q.put(ret)

    def wrap(*args, **kwargs):
        """this is the function returned from the decorator. It fires off
        wrapped_f in a new thread and returns the thread object with
        the result queue attached
        """
        queue_q = queue.Queue()

        thread = threading.Thread(
            target=wrapped_f, args=(queue_q, *args), kwargs=kwargs
        )
        thread.daemon = daemon
        thread.start()
        thread.result_queue = queue
        return thread

    return wrap


class ThreadError(Exception):
    pass


class WorkerProtocol(Protocol):
    def is_completed(self):
        raise NotImplementedError

    def get_result(self):
        raise NotImplementedError

    def execute(self, func, *args, **kwargs):
        raise NotImplementedError

    def set_error_handler(self, handler: Callable) -> None:
        raise NotImplementedError


class WorkerInterface(ABC):
    def __init__(self, job, *args, **kwargs):
        self.job = job
        self.args = args
        self.kwargs = kwargs
        self._status = None

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def is_completed(self):
        pass

    def get_status(self):
        return self._status


class ThreadWorker:
    """Worker is implemented by threading module"""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._result = None
        self._error = Signal()

    def is_completed(self) -> bool:
        if self._thread is None:
            raise ThreadError
        return not self._thread.is_alive()

    def get_result(self) -> Any:
        return self._result

    def set_error_handler(self, handler: Callable) -> None:
        self._error.connect(handler)

    def execute(self, func, *args, **kwargs) -> None:
        self._thread = threading.Thread(
            target=self.wrapper, args=(func, *args), kwargs=kwargs
        )
        self._thread.start()

    def wrapper(self, func, *args, **kwargs) -> None:
        try:
            result = func(*args, **kwargs)
            self._result = result
        except Exception as ex:
            self._error.emit(ex)


class Worker(WorkerInterface):
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
