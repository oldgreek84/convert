import time
import threading
import asyncio
import queue
from concurrent.futures import ThreadPoolExecutor

from functools import wraps, partial

from typing import Generator, Protocol
from abc import ABC, abstractmethod

import requests

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
        '''this function calls the decorated function and puts the
        result in a queue'''
        ret = func(*args, **kwargs)
        wrapped_q.put(ret)

    def wrap(*args, **kwargs):
        '''this is the function returned from the decorator. It fires off
        wrapped_f in a new thread and returns the thread object with
        the result queue attached'''

        queue_q = queue.Queue()

        thread = threading.Thread(target=wrapped_f,
                                  args=(queue_q, ) + args,
                                  kwargs=kwargs)
        thread.daemon = daemon
        thread.start()
        thread.result_queue = queue
        return thread

    return wrap


class WorkerProtocol(Protocol):
    def is_completed(self):
        raise NotImplementedError()

    def get_result(self):
        raise NotImplementedError()

    def execute(self, func, *args, **kwargs):
        raise NotImplementedError()


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


class Worker4:
    """ worker was implemented by threading module"""

    def __init__(self):
        self._thread = None
        self._result = None

    def is_completed(self):
        return not self._thread.is_alive()

    def get_result(self):
        return self._result

    def execute(self, func, *args, **kwargs):
        self._thread = threading.Thread(
            target=self.wrapper,
            args=(func, *args),
            kwargs=kwargs
        )
        self._thread.start()

    def wrapper(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        self._result = result


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

            print(f"----- ST: {self._status}")
            if self.is_completed():
                main_cor.close()
                break

    @coroutine
    def get_some_cor(self):
        while True:
            _, resp_status = self.get_response_status()
            _ = (yield resp_status)

    @coroutine
    def get_status_cor(self):
        try:
            while True:
                run = (yield)
                print(f"1: {run = }")
                if run:
                    res, resp_status = self.job_process(self.args, self.kwargs)
                    print("------------------------------")
                    print(f"response: {res = } {resp_status = }")
                    yield res, resp_status
                    print(f"2: {run = }")
                    print("------------------------------")
                    self._status = res.json()['message']
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
            print("-----", res)
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
                status = (yield)
                # status = next(next_cor)
                print(f"{type(status) = }")
                print(f"waiter: {status = }")
                if isinstance(status, Generator):
                    print("IF--------INSTANCE-")
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
                check = (yield)
                print(f"checker: {check = }")
                if check:
                    time.sleep(3)
                    _, resp_status = self.get_response_status()
                    # waiter_cor.send(resp_status)
                    # yield resp_status
                    waiter.send(resp_status)
        except GeneratorExit:
            print("check coroutine closing...")


class Worker1(WorkerInterface):

    def is_completed(self):
        return self._status in ["error", "completed"]

    def execute(self):
        # self.producer(self.get_status_cor())
        pass

    def main_cor(self):
        pass

    def waiter_cor(self):
        pass

    def checker_cor(self):
        pass


class Worker2(WorkerInterface):

    def is_completed(self):
        return self._status in ["error", "completed"]

    def execute(self):
        self.producer(self.get_status_cor())

    def producer(self, main_cor, until_done=True):
        while True:
            time.sleep(3)
            main_cor.send(True)

            if not until_done:
                break

            print(f"----- ST: {self._status}")
            if self.is_completed():
                main_cor.close()
                break

    @coroutine
    def get_some_cor(self):
        while True:
            _, resp_status = self.get_response_status()
            _ = (yield resp_status)

    @coroutine
    def get_status_cor(self):
        try:
            while True:
                run = (yield)
                print(f"1: {run = }")
                if run:
                    res, resp_status = self.job(*self.args, **self.kwargs)
                    print("------------------------------")
                    print(f"response: {res = } {resp_status = }")
                    print(f"2: {run = }")
                    print("------------------------------")
                    self._status = res.json()['message']
        except GeneratorExit:
            print("closing.........")


class Worker3(WorkerInterface):

    def is_completed(self):
        return self._status in ["error", "completed"]

    def execute(self):
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
            print("-----", res)
        except Exception as ex:
            print(f"{ex = }")

    def checker(self):
        resp_status = False
        while True:
            try:
                time.sleep(3)
                res, resp_status = self.job(*self.args, **self.kwargs)
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
                status = (yield)
                # status = next(next_cor)
                print(f"{type(status) = }")
                print(f"waiter: {status = }")
                if isinstance(status, Generator):
                    print("IF--------INSTANCE-")
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
                check = (yield)
                print(f"checker: {check = }")
                if check:
                    time.sleep(3)
                    _, resp_status = self.get_response_status()
                    # waiter_cor.send(resp_status)
                    # yield resp_status
                    waiter.send(resp_status)
        except GeneratorExit:
            print("check coroutine closing...")


if __name__ == '__main__':

    def get_response_status(some, a):
        print(f"{some = } {a = }")
        res = requests.get("http://localhost:5000/", json={})
        return res, res.json()["status"]["code"]

    # w = Worker()
    # w2 = Worker2()
    # w3 = Worker3()
    w4 = Worker4()
    # w.setup(get_response_status, 11)
    # w2.setup(get_response_status, 11)
    # w3.setup(get_response_status, 11)
    w4.execute(get_response_status, 11, a="a")
