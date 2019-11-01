import random
import re
import string
import threading
import time
from typing import Optional, Tuple

hacking_letters = string.ascii_letters + string.digits


def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", x))


def extract_wallet(content: str) -> Optional[Tuple[str, str]]:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        uuid, key = content.split()
        return uuid, key
    return None


def raw_do_waiting(text: str, status: int):
    status_ident = "|/-\\"[status]
    print(end=f"\r{text} {status_ident}", flush=False)


def do_waiting(message, t):
    pt = 0
    while pt < t:
        for i in range(4):
            raw_do_waiting(message, i)
            time.sleep(0.25)
        pt += 1
    print()


def make_random_message(message: str) -> str:
    return message + " : " + "".join(random.choice(hacking_letters) for _ in range(6))


def do_waiting_hacking(message, t):
    pt = 0
    while pt < t:
        for i in range(4):
            raw_do_waiting(make_random_message(message), i)
            time.sleep(0.25)
        pt += 1
    print()


class DoWaitingHackingThread(threading.Thread):
    def __init__(self, message: str, t: int):
        super().__init__()

        self.message: str = message
        self.t: int = t
        self.running: bool = True
        self.stopped: bool = False

    def run(self):
        pt = 0
        while pt < self.t and self.running:
            for i in range(4):
                raw_do_waiting(make_random_message(self.message), i)
                time.sleep(0.25)
            pt += 1
        self.stopped = True

    def stop(self):
        self.running = False
        while not self.stopped:
            time.sleep(.05)
        print()
