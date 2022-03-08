from pydantic import Field

from .mainboard import Interface
from ..model import Model


class RAM(Model):
    id: int
    size: int = Field(alias="ramSize")
    type: Interface = Field(alias="ramTyp")
    frequency: int
    power: int
