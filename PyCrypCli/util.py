import re
from datetime import datetime
from typing import Optional, Tuple, List

from dateutil.tz import tz


def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", x))


def extract_wallet(content: str) -> Optional[Tuple[str, str]]:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        uuid, key = content.split()
        return uuid, key
    return None


def convert_timestamp(timestamp: datetime) -> datetime:
    return timestamp.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()).replace(tzinfo=None)


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
