from __future__ import annotations

from typing import TYPE_CHECKING

from ..inventory_element import InventoryElement
from ..model import Model
from ..wallet import Wallet

if TYPE_CHECKING:
    from ...client import Client


class ShopProduct(Model):
    id: int
    name: str
    price: int
    related_ms: str

    @staticmethod
    def shop_info(client: Client, product: str) -> ShopProduct:
        return ShopProduct.parse(client, client.ms("inventory", ["shop", "info"], product=product))

    @staticmethod
    def bulk_buy(client: Client, products: dict[ShopProduct, int], wallet: Wallet) -> list[InventoryElement]:
        return [
            InventoryElement.parse(client, element)
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
