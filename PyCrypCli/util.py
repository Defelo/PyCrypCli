import random
import re
import string
import threading
import time
from typing import Optional, Tuple, List

hacking_letters = string.ascii_letters + string.digits


def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", x))


def extract_wallet(content: str) -> Optional[Tuple[str, str]]:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        uuid, key = content.split()
        return uuid, key
    return None


def strip_float(num: float, precision):
    return f"{num:.{precision}f}".rstrip("0").rstrip(".")


def print_tree(items: List[Tuple[str, Optional[list]]], indent: Optional[List[bool]] = None):
    if not indent:
        indent = []
    for i, (item, children) in enumerate(items):
        branch = "└├"[i < len(items) - 1]
        print("".join(" │"[ind] + "   " for ind in indent) + branch + "── " + item)
        if children is not None:
            print_tree(children, indent + [i < len(items) - 1])


def raw_do_waiting(text: str, status: int):
    status_ident = "|/-\\"[status % 4]
    print(end=f"\r{text} {status_ident} ", flush=False)


def make_random_message(message: str) -> str:
    return message + " : " + "".join(random.choice(hacking_letters) for _ in range(6))


def do_waiting_hacking(message, t):
    pt = 0
    while pt < t:
        for i in range(12):
            raw_do_waiting(make_random_message(message), i)
            time.sleep(1 / 12)
        pt += 1
    print()


class DoWaitingHackingThread(threading.Thread):
    def __init__(self, message: str):
        super().__init__()

        self.message: str = message
        self.running: bool = True
        self.stopped: bool = False

    def run(self):
        while self.running:
            for i in range(12):
                raw_do_waiting(make_random_message(self.message), i)
                time.sleep(1 / 12)
        self.stopped = True

    def stop(self):
        self.running = False
        while not self.stopped:
            time.sleep(0.05)
        print()
