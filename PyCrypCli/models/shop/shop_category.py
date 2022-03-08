from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import validator, Field

from .shop_product import ShopProduct
from ..model import Model

if TYPE_CHECKING:
    from ...client import Client


class ShopCategory(Model):
    name: str
    index: int
    items: list[ShopProduct]
    subcategories: list[ShopCategory] = Field(alias="categories")

    @staticmethod
    def shop_list(client: Client) -> list[ShopCategory]:
        out = [
            ShopCategory.parse(client, {"name": k, **v})
            for k, v in client.ms("inventory", ["shop", "list"])["categories"].items()
        ]
        out.sort(key=lambda c: c.index)
        return out

    @validator("items", pre=True)
    def _parse_items(cls, value: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        out = [v | {"name": k} for k, v in value.items()]
        out.sort(key=lambda e: e["id"])
        return out

    @validator("subcategories", pre=True)
    def _parse_subcategories(cls, value: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        out = [v | {"name": k} for k, v in value.items()]
        out.sort(key=lambda e: e["index"])
        return out
