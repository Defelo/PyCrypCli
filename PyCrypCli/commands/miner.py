from typing import List

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import Service, Miner
from PyCrypCli.util import is_uuid


@command(["miner"], [DeviceContext], "Manager your Morphcoin miners")
def handle_miner(context: DeviceContext, args: List[str]):
    if len(args) not in (1, 2) or args[0] not in ("look", "power", "wallet"):
        print("usage: miner look|power|wallet")
        return

    service: Service = context.get_service("miner")
    if service is None:
        print("You have to create the miner service before you can use it.")
        return

    miner: Miner = context.get_client().get_miner(service.uuid)

    if args[0] == "look":
        print("Destination wallet: " + miner.wallet)
        print("Running: " + ["no", "yes"][service.running])
        print(f"Power: {miner.power * 100}%")
        if service.running:
            print(f"Mining speed: {service.speed} MC/s")
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

        try:
            context.get_client().miner_power(service.uuid, power)
        except WalletNotFoundException:
            print("Wallet does not exist.")
    elif args[0] == "wallet":
        if len(args) != 2:
            print("usage: miner wallet <uuid>")
            return

        if not is_uuid(args[1]):
            print("Invalid wallet uuid")
            return

        try:
            context.get_client().miner_wallet(service.uuid, args[1])
        except WalletNotFoundException:
            print("Wallet does not exist.")


@completer([handle_miner])
def miner_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["look", "power", "wallet"]
    elif len(args) == 2:
        if args[0] == "wallet":
            return context.file_path_completer(args[1])
