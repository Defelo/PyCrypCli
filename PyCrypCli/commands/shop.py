from typing import List, Dict

from PyCrypCli.client import Client
from PyCrypCli.commands import command, CommandError
from PyCrypCli.commands.help import print_help
from PyCrypCli.commands.morphcoin import get_wallet_from_file
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import ItemNotFoundException, NotEnoughCoinsException
from PyCrypCli.game_objects import Wallet, ShopCategory, ShopProduct
from PyCrypCli.util import strip_float, print_tree


def list_shop_products(client: Client) -> Dict[str, ShopProduct]:
    out = {}
    for category in ShopCategory.shop_list(client):
        for subcategory in category.subcategories:
            for item in subcategory.items:
                out[item.name.replace(" ", "")] = item
        for item in category.items:
            out[item.name.replace(" ", "")] = item
    return out


@command("shop", [DeviceContext])
def handle_shop(context: DeviceContext, args: List[str]):
    """
    Buy new hardware and more in the shop
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_shop)


@handle_shop.subcommand("list")
def handle_shop_list(context: DeviceContext, _):
    """
    List shop prodcuts
    """

    categories: List[ShopCategory] = ShopCategory.shop_list(context.client)
    maxlength = max(
        *[len(item.name) + 4 for category in categories for item in category.items],
        *[
            len(item.name)
            for category in categories
            for subcategory in category.subcategories
            for item in subcategory.items
        ]
    )
    tree = []
    for category in categories:
        category_tree = []
        for subcategory in category.subcategories:
            subcategory_tree = [
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
def handle_shop_buy(context: DeviceContext, args: List[str]):
    """
    Buy something in the shop
    """

    if len(args) != 2:
        raise CommandError("usage: shop buy <product> <wallet>")

    product_name, wallet_filepath = args

    wallet: Wallet = get_wallet_from_file(context, wallet_filepath)

    shop_products: Dict[str, ShopProduct] = list_shop_products(context.client)
    if product_name not in shop_products:
        raise CommandError("This product does not exist in the shop.")
    product: ShopProduct = shop_products[product_name]

    try:
        product.buy(wallet)
    except ItemNotFoundException:
        raise CommandError("This product does not exist in the shop.")
    except NotEnoughCoinsException:
        raise CommandError("You don't have enough coins on your wallet to buy this product.")


@handle_shop_buy.completer()
def shop_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return list(list_shop_products(context.client))
    if len(args) == 2:
        return context.file_path_completer(args[1])
    return []
