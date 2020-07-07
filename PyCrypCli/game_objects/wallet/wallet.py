from typing import List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.transaction import Transaction
from PyCrypCli.game_objects.wallet.public_wallet import PublicWallet
from PyCrypCli.game_objects.service import Miner


class Wallet(PublicWallet):
    @property
    def key(self) -> str:
        return self._data.get("key")

    @property
    def user(self) -> str:
        return self._data.get("user_uuid")

    @property
    def amount(self) -> int:
        return self._data.get("amount")

    @property
    def transactions(self) -> int:
        return self._data.get("transactions")

    @staticmethod
    def create_wallet(client: Client) -> "Wallet":
        return Wallet(client, client.ms("currency", ["create"]))

    @staticmethod
    def get_wallet(client: Client, uuid: str, key: str) -> "Wallet":
        return Wallet(client, client.ms("currency", ["get"], source_uuid=uuid, key=key))

    def update(self):
        self._update(Wallet.get_wallet(self._client, self.uuid, self.key))

    def get_transactions(self, count: int, offset: int) -> List[Transaction]:
        return [
            Transaction(self._client, t)
            for t in self._ms(
                "currency", ["transactions"], source_uuid=self.uuid, key=self.key, count=count, offset=offset,
            )["transactions"]
        ]

    def get_miners(self) -> List[Miner]:
        return Miner.get_miners(self._client, self.uuid)

    def send(self, destination: PublicWallet, amount: int, usage: str):
        self._ms(
            "currency",
            ["send"],
            source_uuid=self.uuid,
            key=self.key,
            send_amount=amount,
            destination_uuid=destination.uuid,
            usage=usage,
        )
        self.update()

    def delete(self):
        self._ms("currency", ["delete"], source_uuid=self.uuid, key=self.key)
