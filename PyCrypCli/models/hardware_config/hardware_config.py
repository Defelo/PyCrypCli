from pydantic import Field

from .case import Case
from .cpu import CPU
from .disk import Disk
from .gpu import GPU
from .mainboard import Mainboard
from .power_pack import PowerPack
from .processor_cooler import ProcessorCooler
from .ram import RAM
from ..model import Model


class StartPC(Model):
    mainboard: str
    cpu: list[str]
    processor_cooler: list[str] = Field(alias="processorCooler")
    ram: list[str]
    gpu: list[str]
    disk: list[str]
    power_pack: str = Field(alias="powerPack")
    case: str


class HardwareConfig(Model):
    start_pc: StartPC
    mainboard: dict[str, Mainboard]
    cpu: dict[str, CPU]
    processor_cooler: dict[str, ProcessorCooler] = Field(alias="processorCooler")
    ram: dict[str, RAM]
    gpu: dict[str, GPU]
    disk: dict[str, Disk]
    power_pack: dict[str, PowerPack] = Field(alias="powerPack")
    case: dict[str, Case]
