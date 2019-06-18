from typing import List

from commands.command import command
from game import Game


@command(["miner"], "Manager your Morphcoin miners")
def handle_miner(game: Game, args: List[str]):
    if len(args) not in (1, 2) or args[0] not in ("look", "power"):
        print("usage: miner look|power")
        return

    service: dict = game.get_service("miner")
    if service is None:
        print("You have to create the miner service before using it.")
        return

    miner: dict = game.client.get_miner(service["uuid"])

    if args[0] == "look":
        print("Destination wallet: " + miner["wallet"])
        print("Running: " + ["no", "yes"][service["running"]])
        print(f"Power: {miner['power']}%")
    elif args[0] == "power":
        if len(args) != 2:
            print("usage: miner power <percentage>")
            return

        if not args[1].isnumeric() or not 0 <= int(args[1]) <= 100:
            print("percentage has to be an integer between 0 and 100")
            return

        game.client.miner_power(service["uuid"], int(args[1]))
