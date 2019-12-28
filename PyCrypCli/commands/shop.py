from typing import List

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
from PyCrypCli.game_objects import ShopProduct, Wallet
from PyCrypCli.util import strip_float


def label_product_name(hardware: dict, name: str) -> str:
    for key, prod_type in {
        "mainboards": "Mainboard",
        "cpu": "CPU",
        "processorCooler": "Processor Cooler",
        "ram": "RAM",
        "gpu": "GPU",
        "disk": "Disk",
        "powerPack": "Power Pack",
        "case": "Case",
    }.items():
        if (
            isinstance(hardware[key], dict)
            and name in hardware[key]
            or isinstance(hardware[key], list)
            and any(e.get("name") == name for e in hardware[key])
        ):
            return f"{name} ({prod_type})"
    return name


@command(["shop"], [DeviceContext], "Buy new hardware and more in the shop")
def handle_shop(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: shop list|buy")
        return

    if args[0] == "list":
        products: List[ShopProduct] = context.get_client().shop_list()
        hardware: dict = context.get_client().get_hardware_config()
        product_titles: List[str] = [label_product_name(hardware, product.name) for product in products]
        maxlength: int = max(map(len, product_titles))

        for product, product_title in zip(products, product_titles):
            print(f" - {product_title.ljust(maxlength)}  {strip_float(product.price / 1000, 3)} MC")
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

        for product in context.get_client().shop_list():
            if product.name.replace(" ", "") == product_name:
                product_name = product.name
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
            return [product.name.replace(" ", "") for product in context.get_client().shop_list()]
    elif len(args) == 3:
        if args[0] == "buy":
            return context.file_path_completer(args[2])
