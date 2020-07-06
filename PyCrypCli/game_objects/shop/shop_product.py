from typing import Dict, List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject
from PyCrypCli.game_objects.inventory_element import InventoryElement
from PyCrypCli.game_objects.wallet import Wallet


class ShopProduct(GameObject):
    @property
    def name(self) -> str:
        return self._data.get("name")

    @property
    def price(self) -> int:
        return self._data.get("price")

    @property
    def related_ms(self) -> str:
        return self._data.get("related_ms")

    @staticmethod
    def shop_info(client: Client, product: str) -> "ShopProduct":
        return ShopProduct(client, client.ms("inventory", ["shop", "info"], product=product))

    @staticmethod
    def bulk_buy(client: Client, products: Dict["ShopProduct", int], wallet: Wallet) -> List[InventoryElement]:
        return [
            InventoryElement(client, element)
            for element in client.ms(
                "inventory",
                ["shop", "buy"],
                products={k.name: v for k, v in products.items()},
                wallet_uuid=wallet.uuid,
                key=wallet.key,
            )["bought_products"]
        ]

    def buy(self, wallet: Wallet) -> InventoryElement:
        return ShopProduct.bulk_buy(self._client, {self: 1}, wallet)[0]
