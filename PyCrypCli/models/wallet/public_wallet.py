from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ..model import Model

if TYPE_CHECKING:
    from ...client import Client


class PublicWallet(Model):
    uuid: str = Field(alias="source_uuid")

    @staticmethod
    def get_public_wallet(client: Client, uuid: str) -> PublicWallet:
        return PublicWallet.parse(client, {"source_uuid": uuid})

    @staticmethod
    def list_wallets(client: Client) -> list[PublicWallet]:
        return [PublicWallet.get_public_wallet(client, uuid) for uuid in client.ms("currency", ["list"])["wallets"]]

    def reset_wallet(self) -> None:
        self._ms("currency", ["reset"], source_uuid=self.uuid)
