from typing import List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject


class PublicWallet(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("source_uuid")

    @staticmethod
    def get_public_wallet(client: Client, uuid: str) -> "PublicWallet":
        return PublicWallet(client, {"source_uuid": uuid})

    @staticmethod
    def list_wallets(client: Client) -> List["PublicWallet"]:
        return [PublicWallet.get_public_wallet(client, uuid) for uuid in client.ms("currency", ["list"])["wallets"]]

    def reset_wallet(self):
        self._ms("currency", ["reset"], source_uuid=self.uuid)
