from pydantic import Field

from .mainboard import Interface
from ..model import Model


class Disk(Model):
    id: int
    type: str = Field(alias="diskTyp")
    capacity: int
    writing_speed: int = Field(alias="writingSpeed")
    reading_speed: int = Field(alias="readingSpeed")
    interface: Interface
    power: int
