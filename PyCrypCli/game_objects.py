from datetime import datetime
from typing import List, Optional


class GameObject:
    def __repr__(self):
        out: str = self.__class__.__name__ + "("
        out += ", ".join(key + "=" + repr(value) for key, value in self.__dict__.items())
        out += ")"
        return out


class Device(GameObject):
    def __init__(self, uuid: str, name: str, owner: str, powered_on: bool):
        self.uuid: str = uuid
        self.name: str = name
        self.owner: str = owner
        self.powered_on: bool = powered_on

    @staticmethod
    def deserialize(data: dict) -> "Device":
        return Device(data.get("uuid"), data.get("name"), data.get("owner"), data.get("powered_on"))


class File(GameObject):
    def __init__(self, uuid: str, device: str, filename: str, content: str):
        self.uuid: str = uuid
        self.device: str = device
        self.filename: str = filename
        self.content: str = content

    @staticmethod
    def deserialize(data: dict) -> "File":
        return File(data.get("uuid"), data.get("device"), data.get("filename"), data.get("content"))


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
            time_stamp,
            data.get("source_uuid"),
            data.get("destination_uuid"),
            data.get("send_amount"),
            data.get("usage"),
            data.get("origin"),
        )


class Wallet(GameObject):
    def __init__(self, uuid: str, key: str, amount: int, user: str, transactions: List[Transaction]):
        self.uuid: str = uuid
        self.key: str = key
        self.amount: int = amount
        self.user: str = user
        self.transactions: List[Transaction] = transactions

    @staticmethod
    def deserialize(data: dict) -> "Wallet":
        return Wallet(
            data.get("source_uuid"),
            data.get("key"),
            data.get("amount"),
            data.get("user_uuid"),
            [Transaction.deserialize(transaction) for transaction in data.get("transactions")],
        )


class Service(GameObject):
    def __init__(
        self, uuid: str, device: str, owner: str, name: str, running: bool, running_port: int, part_owner: str
    ):
        self.uuid: str = uuid
        self.device: str = device
        self.owner: str = owner
        self.name: str = name
        self.running: bool = running
        self.running_port: int = running_port
        self.part_owner: str = part_owner

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


class ShopProduct(GameObject):
    def __init__(self, name: str, price: int, related_ms: str):
        self.name: str = name
        self.price: int = price
        self.related_ms: str = related_ms

    @staticmethod
    def deserialize(data: dict) -> "ShopProduct":
        return ShopProduct(data.get("name"), data.get("price"), data.get("related_ms"))
