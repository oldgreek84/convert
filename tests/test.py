import time

statuses = ["ready", "processing", "processing", "completed", None]


def main():
    status = some_gen()
    while True:
        time.sleep(1)
        res = next(status)
        print("1---- ")
        print(res)
        if res is None:
            break


def some_gen():
    for s in statuses:
        name = yield s
        print(f"{name = }")
        time.sleep(1)


def simple_coroutine(main_arg):
    print(f"{main_arg = }")

    # idle loop
    try:
        while True:
            out_arg = (yield)
            print(out_arg)
            print("1---- ")
            if out_arg == 12:
                print(f"it`s correct args: {out_arg}")
    except GeneratorExit:
        print("closing...")


def request_cor():
    pass


class Test:
    def __init__(self):
        self.status = "ready"

    def send(self):
        pass

    def get_status(self):
        pass


if __name__ == '__main__':
    # main()
    cor = simple_coroutine("some main arg")
    next(cor)
    cor.send(22)
    cor.send("some")
    cor.send(12)
    cor.close()
