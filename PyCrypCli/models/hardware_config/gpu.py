from pydantic import Field

from .mainboard import Interface
from ..model import Model


class GPU(Model):
    id: int
    ram_size: int = Field(alias="ramSize")
    ram_type: Interface = Field(alias="ramTyp")
    frequency: int
    interface: Interface
    power: int
