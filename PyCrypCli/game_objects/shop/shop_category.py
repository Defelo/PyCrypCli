from typing import List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject
from PyCrypCli.game_objects.shop.shop_product import ShopProduct


class ShopCategory(GameObject):
    @property
    def name(self) -> str:
        return self._data.get("name")

    @property
    def index(self) -> int:
        return self._data.get("index")

    @property
    def items(self) -> List[ShopProduct]:
        return [ShopProduct(self._client, {"name": k, **v}) for k, v in self._data.get("items").items()]

    @property
    def subcategories(self) -> List["ShopCategory"]:
        out = [ShopCategory(self._client, {"name": k, **v}) for k, v in self._data.get("categories").items()]
        out.sort(key=lambda c: c.index)
        return out

    @staticmethod
    def shop_list(client: Client) -> List["ShopCategory"]:
        out = [
            ShopCategory(client, {"name": k, **v})
            for k, v in client.ms("inventory", ["shop", "list"])["categories"].items()
        ]
        out.sort(key=lambda c: c.index)
        return out
