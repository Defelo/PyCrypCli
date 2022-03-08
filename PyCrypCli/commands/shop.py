from typing import Any

from .command import command, CommandError
from .help import print_help
from .morphcoin import get_wallet_from_file
from ..client import Client
from ..context import DeviceContext
from ..exceptions import ItemNotFoundError, NotEnoughCoinsError
from ..models import Wallet, ShopCategory, ShopProduct
from ..util import strip_float, print_tree


def list_shop_products(client: Client) -> dict[str, ShopProduct]:
    out = {}
    for category in ShopCategory.shop_list(client):
        for subcategory in category.subcategories:
            for item in subcategory.items:
                out[item.name.replace(" ", "")] = item
        for item in category.items:
            out[item.name.replace(" ", "")] = item
    return out


@command("shop", [DeviceContext])
def handle_shop(context: DeviceContext, args: list[str]) -> None:
    """
    Buy new hardware and more in the shop
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_shop)


@handle_shop.subcommand("list")
def handle_shop_list(context: DeviceContext, _: Any) -> None:
    """
    List shop prodcuts
    """

    categories: list[ShopCategory] = ShopCategory.shop_list(context.client)
    maxlength = max(
        *[len(item.name) + 4 for category in categories for item in category.items],
        *[
            len(item.name)
            for category in categories
            for subcategory in category.subcategories
            for item in subcategory.items
        ],
    )
    tree = []
    for category in categories:
        category_tree = []
        for subcategory in category.subcategories:
            subcategory_tree: list[tuple[str, list[Any]]] = [
                (item.name.ljust(maxlength) + strip_float(item.price / 1000, 3) + " MC", [])
                for item in subcategory.items
            ]
            category_tree.append((subcategory.name, subcategory_tree))

        for item in category.items:
            category_tree.append((item.name.ljust(maxlength + 4) + strip_float(item.price / 1000, 3) + " MC", []))

        tree.append((category.name, category_tree))

    print("Shop")
    print_tree(tree)


@handle_shop.subcommand("buy")
def handle_shop_buy(context: DeviceContext, args: list[str]) -> None:
    """
    Buy something in the shop
    """

    if len(args) != 2:
        raise CommandError("usage: shop buy <product> <wallet>")

    product_name, wallet_filepath = args

    wallet: Wallet = get_wallet_from_file(context, wallet_filepath)

    shop_products: dict[str, ShopProduct] = list_shop_products(context.client)
    if product_name not in shop_products:
        raise CommandError("This product does not exist in the shop.")
    product: ShopProduct = shop_products[product_name]

    try:
        product.buy(wallet)
    except ItemNotFoundError:
        raise CommandError("This product does not exist in the shop.")
    except NotEnoughCoinsError:
        raise CommandError("You don't have enough coins on your wallet to buy this product.")


@handle_shop_buy.completer()
def shop_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return list(list_shop_products(context.client))
    if len(args) == 2:
        return context.file_path_completer(args[1])
    return []
