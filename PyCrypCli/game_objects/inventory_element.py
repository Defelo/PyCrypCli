from typing import List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject


class InventoryElement(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("element_uuid")

    @property
    def name(self) -> str:
        return self._data.get("element_name")

    @property
    def related_ms(self) -> str:
        return self._data.get("related_ms")

    @property
    def owner(self) -> str:
        return self._data.get("owner")

    @staticmethod
    def list_inventory(client: Client) -> List["InventoryElement"]:
        return [
            InventoryElement(client, element) for element in client.ms("inventory", ["inventory", "list"])["elements"]
        ]

    def trade(self, target: str):
        self._ms("inventory", ["inventory", "trade"], element_uuid=self.uuid, target=target)
