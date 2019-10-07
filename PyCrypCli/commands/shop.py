from typing import List

from PyCrypCli.commands.command import CTX_DEVICE, command
from PyCrypCli.exceptions import (
    FileNotFoundException,
    InvalidWalletFile,
    UnknownSourceOrDestinationException,
    PermissionDeniedException,
    ItemNotFoundException,
    NotEnoughCoinsException,
)
from PyCrypCli.game import Game
from PyCrypCli.game_objects import ShopProduct, Wallet


@command(["shop"], CTX_DEVICE, "Buy new hardware and more in the shop")
def handle_shop(game: Game, _, args: List[str]):
    if not args:
        print("usage: shop list|buy")
        return

    if args[0] == "list":
        product_names: List[str] = game.client.shop_list()
        maxlength: int = max(map(len, product_names))
        for product_name in game.client.shop_list():
            product: ShopProduct = game.client.shop_info(product_name)
            print(" - " + product.name.ljust(maxlength + 2) + f"{product.price} MC")
    elif args[0] == "buy":
        if len(args) not in (3, 4):
            print("usage: shop buy <product> <wallet>")
            return

        product_name, wallet_filename = args[1:]

        try:
            wallet: Wallet = game.get_wallet_from_file(wallet_filename)
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

        for name in game.client.shop_list():
            if name.replace(" ", "") == product_name:
                product_name = name
                break
        else:
            print("This product does not exist in the shop.")
            return

        try:
            game.client.shop_buy(product_name, wallet.uuid, wallet.key)
        except ItemNotFoundException:
            print("This product does not exist in the shop.")
        except NotEnoughCoinsException:
            print("You don't have enough coins on your wallet to buy this product.")
    else:
        print("usage: shop list|buy")
