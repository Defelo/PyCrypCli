from pydantic import Field

from .mainboard import GraphicUnit
from ..model import Model


class CPU(Model):
    id: int
    frequency_min: int = Field(alias="frequencyMin")
    frequency_max: int = Field(alias="frequencyMax")
    socket: str
    cores: int
    turbo_speed: bool = Field(alias="turboSpeed")
    overclock: bool = Field(alias="overClock")
    max_temperature: int = Field(alias="maxTemperature")
    graphic_unit: GraphicUnit | None = Field(alias="graphicUnit")
    power: int
