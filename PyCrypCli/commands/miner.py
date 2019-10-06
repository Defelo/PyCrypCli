from typing import List

from ..commands.command import command, CTX_DEVICE
from ..exceptions import *
from ..game import Game
from ..game_objects import Service, Miner
from ..util import is_uuid


@command(["miner"], CTX_DEVICE, "Manager your Morphcoin miners")
def handle_miner(game: Game, _, args: List[str]):
    if len(args) not in (1, 2) or args[0] not in ("look", "power", "wallet"):
        print("usage: miner look|power|wallet")
        return

    service: Service = game.get_service("miner")
    if service is None:
        print("You have to create the miner service before you can use it.")
        return

    miner: Miner = game.client.get_miner(service.uuid)

    if args[0] == "look":
        print("Destination wallet: " + miner.wallet)
        print("Running: " + ["no", "yes"][service.running])
        print(f"Power: {miner.power * 100}%")
    elif args[0] == "power":
        if len(args) != 2:
            print("usage: miner power <percentage>")
            return

        try:
            power: float = float(args[1]) / 100
            if not 0 <= power <= 1:
                raise ValueError
        except ValueError:
            print("percentage has to be an integer between 0 and 100")
            return

        game.client.miner_power(service.uuid, power)
    elif args[0] == "wallet":
        if len(args) != 2:
            print("usage: miner wallet <uuid>")
            return

        if not is_uuid(args[1]):
            print("Invalid wallet uuid")
            return

        try:
            game.client.miner_wallet(service.uuid, args[1])
        except WalletNotFoundException:
            print("Wallet does not exist.")
