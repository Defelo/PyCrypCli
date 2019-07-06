from datetime import datetime
from typing import List, Optional


class Device:
    def __init__(self, uuid: str, name: str, owner: str, power: int, powered_on: bool):
        self.uuid: str = uuid
        self.name: str = name
        self.owner: str = owner
        self.power: int = power
        self.powered_on: bool = powered_on

    @staticmethod
    def deserialize(data: dict) -> 'Device':
        return Device(
            data.get("uuid"),
            data.get("name"),
            data.get("owner"),
            data.get("power"),
            data.get("powered_on")
        )


class File:
    def __init__(self, uuid: str, device: str, filename: str, content: str):
        self.uuid: str = uuid
        self.device: str = device
        self.filename: str = filename
        self.content: str = content

    @staticmethod
    def deserialize(data: dict) -> 'File':
        return File(
            data.get("uuid"),
            data.get("device"),
            data.get("filename"),
            data.get("content")
        )


class Transaction:
    def __init__(self, time_stamp: datetime, source_uuid: str, destination_uuid: str, amount: int,
                 usage: str, origin: int):
        self.time_stamp: datetime = time_stamp
        self.source_uuid: str = source_uuid
        self.destination_uuid: str = destination_uuid
        self.amount: int = amount
        self.usage: str = usage
        self.origin: int = origin

    @staticmethod
    def deserialize(data: dict) -> 'Transaction':
        time_stamp: Optional[str] = data.get("time_stamp")
        if time_stamp is not None:
            time_stamp: datetime = datetime.fromisoformat(time_stamp)

        return Transaction(
            time_stamp,
            data.get("source_uuid"),
            data.get("destination_uuid"),
            data.get("send_amount"),
            data.get("usage"),
            data.get("origin")
        )


class Wallet:
    def __init__(self, uuid: str, key: str, amount: int, user: str, transactions: List[Transaction]):
        self.uuid: str = uuid
        self.key: str = key
        self.amount: int = amount
        self.user: str = user
        self.transactions: List[Transaction] = transactions

    @staticmethod
    def deserialize(data: dict) -> 'Wallet':
        return Wallet(
            data.get("source_uuid"),
            data.get("key"),
            data.get("amount"),
            data.get("user_uuid"),
            [Transaction.deserialize(transaction) for transaction in data.get("transactions")]
        )
