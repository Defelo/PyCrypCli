from typing import NamedTuple

from pydantic import Field

from ..model import Model

Interface = NamedTuple("Interface", [("name", str), ("version", int)])


class RAM(Model):
    ram_slots: int = Field(alias="ramSlots")
    max_ram_size: int = Field(alias="maxRamSize")
    ram_type: list[Interface] = Field(alias="ramTyp")
    frequency: list[int]


class GraphicUnit(Model):
    name: str
    ram_size: int = Field(alias="ramSize")
    frequency: int


class ExpansionSlot(Model):
    interface: Interface
    interface_slots: int = Field(alias="interfaceSlots")


class DiskStorage(Model):
    disk_slots: int = Field(alias="diskSlots")
    interface: list[Interface]


class NetworkPort(Model):
    name: str
    interface: str
    speed: int


class Mainboard(Model):
    id: int
    case: str
    cpu_socket: str = Field(alias="cpuSocket")
    cpu_slots: int = Field(alias="cpuSlots")
    core_temperature_control: bool = Field(alias="coreTemperatureControl")
    usb_ports: int = Field(alias="usbPorts")
    graphic_unit_on_board: GraphicUnit = Field(alias="graphicUnitOnBoard")
    expansion_slots: list[ExpansionSlot] = Field(alias="expansionSlots")
    disk_storage: DiskStorage = Field(alias="diskStorage")
    network_port: NetworkPort = Field(alias="NetworkPort")
    power: int
