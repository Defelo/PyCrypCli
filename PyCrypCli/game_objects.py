from datetime import datetime
from typing import Optional, List

from dateutil import tz


class GameObject:
    def __repr__(self):
        out: str = self.__class__.__name__ + "("
        out += ", ".join(key + "=" + repr(value) for key, value in self.__dict__.items())
        out += ")"
        return out

    @staticmethod
    def deserialize(data: dict):
        pass


class Device(GameObject):
    def __init__(self, uuid: str, name: str, owner: str, powered_on: bool):
        self.uuid: str = uuid
        self.name: str = name
        self.owner: str = owner
        self.powered_on: bool = powered_on

    @staticmethod
    def deserialize(data: dict) -> "Device":
        return Device(data.get("uuid"), data.get("name"), data.get("owner"), data.get("powered_on"))


class DeviceHardware(GameObject):
    def __init__(self, uuid: str, device_uuid: str, hardware_element: str, hardware_type: str):
        self.uuid: str = uuid
        self.device_uuid: str = device_uuid
        self.hardware_element: str = hardware_element
        self.hardware_type: str = hardware_type

    @staticmethod
    def deserialize(data: dict) -> "DeviceHardware":
        return DeviceHardware(
            data.get("uuid"), data.get("device_uuid"), data.get("hardware_element"), data.get("hardware_type")
        )


class File(GameObject):
    def __init__(
        self,
        uuid: Optional[str],
        device: str,
        filename: Optional[str],
        content: Optional[str],
        is_directory: bool,
        parent_dir_uuid: Optional[str],
    ):
        self.uuid: str = uuid
        self.device: str = device
        self.filename: str = filename
        self.content: str = content
        self.is_directory: bool = is_directory
        self.parent_dir_uuid: str = parent_dir_uuid

    @staticmethod
    def deserialize(data: dict) -> "File":
        return File(
            data.get("uuid"),
            data.get("device"),
            data.get("filename"),
            data.get("content"),
            data.get("is_directory"),
            data.get("parent_dir_uuid"),
        )


class Transaction(GameObject):
    def __init__(
        self, time_stamp: datetime, source_uuid: str, destination_uuid: str, amount: int, usage: str, origin: int
    ):
        self.time_stamp: datetime = time_stamp
        self.source_uuid: str = source_uuid
        self.destination_uuid: str = destination_uuid
        self.amount: int = amount
        self.usage: str = usage
        self.origin: int = origin

    @staticmethod
    def deserialize(data: dict) -> "Transaction":
        time_stamp: Optional[str] = data.get("time_stamp")
        if time_stamp is not None:
            time_stamp: datetime = datetime.fromisoformat(time_stamp)

        return Transaction(
            time_stamp.replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()),
            data.get("source_uuid"),
            data.get("destination_uuid"),
            data.get("send_amount"),
            data.get("usage"),
            data.get("origin"),
        )


class Wallet(GameObject):
    def __init__(self, uuid: str, key: str, amount: int, user: str, transactions: int):
        self.uuid: str = uuid
        self.key: str = key
        self.amount: int = amount
        self.user: str = user
        self.transactions: int = transactions

    @staticmethod
    def deserialize(data: dict) -> "Wallet":
        return Wallet(
            data.get("source_uuid"),
            data.get("key"),
            data.get("amount"),
            data.get("user_uuid"),
            data.get("transactions"),
        )


class Service(GameObject):
    def __init__(
        self,
        uuid: str,
        device: str,
        owner: str,
        name: str,
        running: bool,
        running_port: int,
        part_owner: str,
        speed: float,
    ):
        self.uuid: str = uuid
        self.device: str = device
        self.owner: str = owner
        self.name: str = name
        self.running: bool = running
        self.running_port: int = running_port
        self.part_owner: str = part_owner
        self.speed: float = speed

    @staticmethod
    def deserialize(data: dict) -> "Service":
        return Service(
            data.get("uuid"),
            data.get("device"),
            data.get("owner"),
            data.get("name"),
            data.get("running"),
            data.get("running_port"),
            data.get("part_owner"),
            data.get("speed"),
        )


class Miner(GameObject):
    def __init__(self, uuid: str, wallet: str, started: int, power: float):
        self.uuid: str = uuid
        self.wallet: str = wallet
        self.started: int = started
        self.power: float = power

    @staticmethod
    def deserialize(data: dict) -> "Miner":
        return Miner(data.get("uuid"), data.get("wallet"), data.get("started"), data.get("power"))


class InventoryElement(GameObject):
    def __init__(self, element_uuid: str, element_name: str, related_ms: str, owner: str):
        self.element_uuid: str = element_uuid
        self.element_name: str = element_name
        self.related_ms: str = related_ms
        self.owner: str = owner

    @staticmethod
    def deserialize(data: dict) -> "InventoryElement":
        return InventoryElement(
            data.get("element_uuid"), data.get("element_name"), data.get("related_ms"), data.get("owner")
        )


class ShopCategory(GameObject):
    def __init__(self, name: str, index: int, items: List["ShopProduct"], subcategories: List["ShopCategory"]):
        self.name = name
        self.index = index
        self.items = items
        self.subcategories = subcategories
        self.subcategories.sort(key=lambda c: c.index)

    @staticmethod
    def deserialize(data: dict) -> "ShopCategory":
        return ShopCategory(
            data.get("name"),
            data.get("index"),
            [ShopProduct.deserialize({"name": k, **v}) for k, v in data.get("items").items()],
            [ShopCategory.deserialize({"name": k, **v}) for k, v in data.get("categories").items()],
        )


class ShopProduct(GameObject):
    def __init__(self, name: str, price: int, related_ms: str):
        self.name: str = name
        self.price: int = price
        self.related_ms: str = related_ms

    @staticmethod
    def deserialize(data: dict) -> "ShopProduct":
        return ShopProduct(data.get("name"), data.get("price"), data.get("related_ms"))


class ResourceUsage(GameObject):
    def __init__(self, cpu: float, ram: float, gpu: float, disk: float, network: float):
        self.cpu: float = cpu
        self.ram: float = ram
        self.gpu: float = gpu
        self.disk: float = disk
        self.network: float = network

    @staticmethod
    def deserialize(data: dict) -> "ResourceUsage":
        return ResourceUsage(data.get("cpu"), data.get("ram"), data.get("gpu"), data.get("disk"), data.get("network"))


class Network(GameObject):
    def __init__(self, uuid: str, hidden: bool, owner: str, name: str):
        self.uuid: str = uuid
        self.hidden: bool = hidden
        self.owner: str = owner
        self.name: str = name

    @staticmethod
    def deserialize(data: dict) -> "Network":
        return Network(data.get("uuid"), data.get("hidden"), data.get("owner"), data.get("name"))


class NetworkMembership(GameObject):
    def __init__(self, uuid: str, network: str, device: str):
        self.uuid: str = uuid
        self.network: str = network
        self.device: str = device

    @staticmethod
    def deserialize(data: dict) -> "NetworkMembership":
        return NetworkMembership(data.get("uuid"), data.get("network"), data.get("device"))


class NetworkInvitation(GameObject):
    def __init__(self, uuid: str, network: str, device: str, request: bool):
        self.uuid: str = uuid
        self.network: str = network
        self.device: str = device
        self.request: bool = request

    @staticmethod
    def deserialize(data: dict) -> "NetworkInvitation":
        return NetworkInvitation(data.get("uuid"), data.get("network"), data.get("device"), data.get("request"))
