from collections import Counter
from typing import List, Dict, Any

from .command import CommandError, command
from .help import print_help
from ..context import MainContext, DeviceContext
from ..exceptions import CannotTradeWithYourselfError, UserUUIDDoesNotExistError
from ..models import InventoryElement, ShopCategory
from ..util import print_tree


@command("inventory", [MainContext, DeviceContext])
def handle_inventory(context: MainContext, args: List[str]) -> None:
    """
    Manage your inventory and trade with other players
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_inventory)


@handle_inventory.subcommand("list")
def handle_inventory_list(context: MainContext, _: Any) -> None:
    """
    List your inventory
    """

    inventory: Dict[str, int] = Counter(element.name for element in InventoryElement.list_inventory(context.client))
    if not inventory:
        raise CommandError("Your inventory is empty.")

    categories: List[ShopCategory] = ShopCategory.shop_list(context.client)
    tree = []
    for category in categories:
        category_tree = []
        for subcategory in category.subcategories:
            subcategory_tree: list[tuple[str, list[Any]]] = [
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
def handle_inventory_trade(context: MainContext, args: List[str]) -> None:
    """
    Trade with other players
    """

    if len(args) != 2:
        raise CommandError("usage: inventory trade <item> <user>")

    item_name, target_user = args

    for item in InventoryElement.list_inventory(context.client):
        if item.name.replace(" ", "") == item_name:
            break
    else:
        raise CommandError("You do not own this item.")

    try:
        item.trade(target_user)
    except CannotTradeWithYourselfError:
        raise CommandError("You cannot trade with yourself.")
    except UserUUIDDoesNotExistError:
        raise CommandError("This user does not exist.")


@handle_inventory_trade.completer()
def inventory_completer(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return [element.name.replace(" ", "") for element in InventoryElement.list_inventory(context.client)]
    return []
