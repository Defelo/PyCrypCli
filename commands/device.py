from typing import List

from commands.command import command
from game import Game


@command(["hostname"], "Show or modify the name of the device")
def handle_hostname(game: Game, args: List[str]):
    if args:
        name: str = " ".join(args)
        if not name:
            print("The name must not be empty.")
            return
        if len(name) > 15:
            print("The name cannot be longer than 15 characters.")
            return
        game.client.change_device_name(game.device_uuid, name)
    game.update_host(game.device_uuid)
    if not args:
        print(game.hostname)
