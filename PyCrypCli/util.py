import re
from datetime import datetime, timezone
from typing import Any, Sequence


def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", x))


def extract_wallet(content: str) -> tuple[str, str] | None:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        uuid, key = content.split()
        return uuid, key
    return None


def utc_to_local(timestamp: datetime) -> datetime:
    return timestamp.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)


def strip_float(num: float, precision: int) -> str:
    return f"{num:.{precision}f}".rstrip("0").rstrip(".")


def print_tree(items: Sequence[tuple[str, Sequence[Any] | None]], indent: list[bool] | None = None) -> None:
    if not indent:
        indent = []
    for i, (item, children) in enumerate(items):
        branch = "└├"[i < len(items) - 1]
        print("".join(" │"[ind] + "   " for ind in indent) + branch + "── " + item)
        if children is not None:
            print_tree(children, indent + [i < len(items) - 1])
