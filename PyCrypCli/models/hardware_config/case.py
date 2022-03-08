from typing import Literal

from ..model import Model


class Case(Model):
    id: int
    size: Literal["small", "middle", "big"]
