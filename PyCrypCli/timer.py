import time
from threading import Thread
from typing import Callable, Any


class Timer(Thread):
    def __init__(self, interval: float, func: Callable[[], Any]):
        super().__init__(daemon=True)

        self.interval: float = interval
        self.func: Callable[[], Any] = func
        self.running: bool = False

    def run(self) -> None:
        self.running = True
        while self.running:
            self.func()

            t: float = time.time()
            sleep_until: float = t + self.interval
            while t < sleep_until and self.running:
                time.sleep(min(0.1, sleep_until - t))
                t = time.time()

    def stop(self) -> None:
        self.running = False
