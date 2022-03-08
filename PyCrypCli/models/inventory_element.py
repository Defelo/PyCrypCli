from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .model import Model

if TYPE_CHECKING:
    from ..client import Client


class InventoryElement(Model):
    uuid: str = Field(alias="element_uuid")
    name: str = Field(alias="element_name")
    related_ms: str
    owner_uuid: str = Field(alias="owner")

    @staticmethod
    def list_inventory(client: Client) -> list[InventoryElement]:
        return [
            InventoryElement.parse(client, element)
            for element in client.ms("inventory", ["inventory", "list"])["elements"]
        ]

    def trade(self, target: str) -> None:
        self._ms("inventory", ["inventory", "trade"], element_uuid=self.uuid, target=target)
