from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .public_wallet import PublicWallet
from .transaction import Transaction
from ..service import Miner

if TYPE_CHECKING:
    from ...client import Client


class Wallet(PublicWallet):
    key: str
    owner_uuid: str = Field(alias="user_uuid")
    amount: int
    transaction_count: int = Field(alias="transactions")

    @staticmethod
    def create_wallet(client: Client) -> Wallet:
        return Wallet.parse(client, client.ms("currency", ["create"]))

    @staticmethod
    def get_wallet(client: Client, uuid: str, key: str) -> Wallet:
        return Wallet.parse(client, client.ms("currency", ["get"], source_uuid=uuid, key=key))

    def update(self) -> Wallet:
        return self._update(Wallet.get_wallet(self._client, self.uuid, self.key))

    def get_transactions(self, count: int, offset: int) -> list[Transaction]:
        return [
            Transaction.parse(self._client, t)
            for t in self._ms(
                "currency", ["transactions"], source_uuid=self.uuid, key=self.key, count=count, offset=offset
            )["transactions"]
        ]

    def get_miners(self) -> list[Miner]:
        return Miner.get_miners(self._client, self.uuid)

    def get_mining_rate(self) -> float:
        return sum(miner.speed for miner in self.get_miners() if miner.running)

    def send(self, destination: PublicWallet, amount: int, usage: str) -> Wallet:
        self._ms(
            "currency",
            ["send"],
            source_uuid=self.uuid,
            key=self.key,
            send_amount=amount,
            destination_uuid=destination.uuid,
            usage=usage,
        )
        return self.update()

    def delete(self) -> None:
        self._ms("currency", ["delete"], source_uuid=self.uuid, key=self.key)
