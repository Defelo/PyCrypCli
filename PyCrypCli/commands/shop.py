from typing import List

from PyCrypCli.client import Client

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import (
    FileNotFoundException,
    InvalidWalletFile,
    UnknownSourceOrDestinationException,
    PermissionDeniedException,
    ItemNotFoundException,
    NotEnoughCoinsException,
)
from PyCrypCli.game_objects import Wallet, ShopCategory
from PyCrypCli.util import strip_float, print_tree


def list_shop_products(client: Client) -> List[str]:
    out = []
    for category in client.shop_list():
        for subcategory in category.subcategories:
            out += [item.name for item in subcategory.items]
        out += [item.name for item in category.items]
    return out


@command(["shop"], [DeviceContext], "Buy new hardware and more in the shop")
def handle_shop(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: shop list|buy")
        return

    if args[0] == "list":
        categories: List[ShopCategory] = context.get_client().shop_list()
        maxlength = max(
            [len(item.name) + 4 for category in categories for item in category.items]
            + [
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
    elif args[0] == "buy":
        if len(args) not in (3, 4):
            print("usage: shop buy <product> <wallet>")
            return

        product_name, wallet_filepath = args[1:]

        try:
            wallet: Wallet = context.get_wallet_from_file(wallet_filepath)
        except FileNotFoundException:
            print("File does not exist.")
            return
        except InvalidWalletFile:
            print("File is no wallet file.")
            return
        except UnknownSourceOrDestinationException:
            print("Invalid wallet file. Wallet does not exist.")
            return
        except PermissionDeniedException:
            print("Invalid wallet file. Key is incorrect.")
            return

        for product in list_shop_products(context.get_client()):
            if product.replace(" ", "") == product_name:
                product_name = product
                break
        else:
            print("This product does not exist in the shop.")
            return

        try:
            context.get_client().shop_buy({product_name: 1}, wallet.uuid, wallet.key)
        except ItemNotFoundException:
            print("This product does not exist in the shop.")
        except NotEnoughCoinsException:
            print("You don't have enough coins on your wallet to buy this product.")
    else:
        print("usage: shop list|buy")


@completer([handle_shop])
def shop_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["list", "buy"]
    elif len(args) == 2:
        if args[0] == "buy":
            return [product.replace(" ", "") for product in list_shop_products(context.get_client())]
    elif len(args) == 3:
        if args[0] == "buy":
            return context.file_path_completer(args[2])
