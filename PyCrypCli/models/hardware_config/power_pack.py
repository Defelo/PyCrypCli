from pydantic import Field

from ..model import Model


class PowerPack(Model):
    id: int
    total_power: int = Field(alias="totalPower")
