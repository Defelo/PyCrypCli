from collections import Counter
from typing import List, Dict

from PyCrypCli.commands.command import command
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import MainContext, DeviceContext
from PyCrypCli.exceptions import CannotTradeWithYourselfException, UserUUIDDoesNotExistException
from PyCrypCli.game_objects import InventoryElement, ShopCategory
from PyCrypCli.util import print_tree


@command("inventory", [MainContext, DeviceContext])
def handle_inventory(context: MainContext, args: List[str]):
    """
    Manage your inventory and trade with other players
    """

    if args:
        print("Unknown subcommand.")
    else:
        print_help(context, handle_inventory)


@handle_inventory.subcommand("list")
def handle_inventory_list(context: MainContext, _):
    """
    List your inventory
    """

    inventory: Dict[str, int] = Counter(element.element_name for element in context.get_client().inventory_list())
    if not inventory:
        print("Your inventory is empty.")
        return

    categories: List[ShopCategory] = context.get_client().shop_list()
    tree = []
    for category in categories:
        category_tree = []
        for subcategory in category.subcategories:
            subcategory_tree = [
                (f"{inventory[item.name]}x {item.name}", []) for item in subcategory.items if inventory[item.name]
            ]
            if subcategory_tree:
                category_tree.append((subcategory.name, subcategory_tree))

        for item in category.items:
            if inventory[item.name]:
                category_tree.append((f"{inventory[item.name]}x {item.name}", []))

        if category_tree:
            tree.append((category.name, category_tree))

    print("Inventory")
    print_tree(tree)


@handle_inventory.subcommand("trade")
def handle_inventory_trade(context: MainContext, args: List[str]):
    """
    Trade with other players
    """

    if len(args) != 2:
        print("usage: inventory trade <item> <user>")
        return

    item_name, target_user = args

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


@handle_inventory_trade.completer()
def inventory_completer(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return [element.element_name.replace(" ", "") for element in context.get_client().inventory_list()]
