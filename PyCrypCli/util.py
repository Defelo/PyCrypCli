import re
import sys
import time
import random

from typing import Optional, Tuple

hacking_letters = list("ABCDEFGHIKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyt123457890")

def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", x))


def extract_wallet(content: str) -> Optional[Tuple[str, str]]:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        uuid, key = content.split()
        return uuid, key
    return None
def raw_do_waiting(writing_text, status):
    status_ident = '|'
    if status == 2:
        status_ident = '/'
    elif status == 3:
        status_ident = '-'
    elif status == 4:
        status_ident = '\\'

    sys.stdout.write(f'\r{writing_text} {status_ident}')

def do_waiting(message, t):
    pt = 0
    while pt < t:
        raw_do_waiting(message, 1)
        time.sleep(0.25)
        raw_do_waiting(message, 2)
        time.sleep(0.25)
        raw_do_waiting(message, 3)
        time.sleep(0.25)
        raw_do_waiting(message, 4)
        time.sleep(0.25)
        pt += 1
    print("")
def make_random_message (message: str) -> str:
    message += " : "
    for i in range(6):
        message += random.choice(hacking_letters)
    return message

def do_waiting_hacking(message, t):
    pt = 0
    while pt < t:
        raw_do_waiting(make_random_message(message), 1)
        time.sleep(0.25)
        raw_do_waiting(make_random_message(message), 2)
        time.sleep(0.25)
        raw_do_waiting(make_random_message(message), 3)
        time.sleep(0.25)
        raw_do_waiting(make_random_message(message), 4)
        time.sleep(0.25)
        pt += 1
    print("")