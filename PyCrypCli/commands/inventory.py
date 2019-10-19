from collections import Counter
from typing import List, Tuple

from PyCrypCli.commands.command import command, completer
from PyCrypCli.commands.shop import label_product_name
from PyCrypCli.context import MainContext, DeviceContext
from PyCrypCli.exceptions import CannotTradeWithYourselfException, UserUUIDDoesNotExistException
from PyCrypCli.game_objects import InventoryElement


@command(["inventory"], [MainContext, DeviceContext], "Manage your inventory and trade with other players")
def handle_inventory(context: MainContext, args: List[str]):
    if not args:
        print("usage: inventory list|trade")
        return

    if args[0] == "list":
        inventory: List[Tuple[str, int]] = Counter(
            element.element_name for element in context.get_client().inventory_list()
        ).most_common()

        if not inventory:
            print("Your inventory is empty.")
            return

        hardware: dict = context.get_client().get_hardware_config()
        print("Your inventory:")
        for element_name, count in inventory:
            print(f" - {count}x {label_product_name(hardware, element_name)}")
    elif args[0] == "trade":
        if len(args) != 3:
            print("usage: inventory trade <item> <user>")
            return

        item_name, target_user = args[1:]

        for item in context.get_client().inventory_list():
            if item.element_name.replace(" ", "") == item_name:
                element: InventoryElement = item
                break
        else:
            print("You do not own this item.")
            return

        try:
            context.get_client().inventory_trade(element.element_uuid, target_user)
        except CannotTradeWithYourselfException:
            print("You cannot trade with yourself.")
        except UserUUIDDoesNotExistException:
            print("This user does not exist.")
    else:
        print("usage: inventory list|trade")


@completer([handle_inventory])
def inventory_completer(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["list", "trade"]
    elif len(args) == 2:
        if args[0] == "trade":
            return [element.element_name.replace(" ", "") for element in context.get_client().inventory_list()]
