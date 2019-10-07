from collections import Counter
from typing import List, Tuple

from PyCrypCli.commands.command import CTX_MAIN, CTX_DEVICE, command
from PyCrypCli.exceptions import CannotTradeWithYourselfException, UserUUIDDoesNotExistException
from PyCrypCli.game import Game
from PyCrypCli.game_objects import InventoryElement


@command(["inventory"], CTX_MAIN | CTX_DEVICE, "Manage your inventory and trade with other players")
def handle_inventory(game: Game, _, args: List[str]):
    if not args:
        print("usage: inventory list|trade")
        return

    if args[0] == "list":
        inventory: List[Tuple[str, int]] = Counter(
            element.element_name for element in game.client.inventory_list()
        ).most_common()

        if not inventory:
            print("Your inventory is empty.")
        else:
            print("Your inventory:")
        for element, count in inventory:
            print(f" - {count}x {element}")
    elif args[0] == "trade":
        if len(args) != 3:
            print("usage: inventory trade <item> <user>")
            return

        item_name, target_user = args[1:]

        for item in game.client.inventory_list():
            if item.element_name.replace(" ", "") == item_name:
                element: InventoryElement = item
                break
        else:
            print("You do not own this item.")
            return

        try:
            game.client.inventory_trade(element.element_uuid, target_user)
        except CannotTradeWithYourselfException:
            print("You cannot trade with yourself.")
        except UserUUIDDoesNotExistException:
            print("This user does not exist.")
    else:
        print("usage: inventory list|trade")
