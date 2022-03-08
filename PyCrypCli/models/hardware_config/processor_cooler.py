from pydantic import Field

from ..model import Model


class ProcessorCooler(Model):
    id: int
    speed: int = Field(alias="coolerSpeed")
    socket: str
    power: int
