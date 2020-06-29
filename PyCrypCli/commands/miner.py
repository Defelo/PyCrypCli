from typing import List

from PyCrypCli.commands.command import command
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import Service, Miner
from PyCrypCli.util import is_uuid


@command("miner", [DeviceContext])
def handle_miner(context: DeviceContext, args: List[str]):
    """
    Manager your Morphcoin miners
    """

    if args:
        print("Unknown subcommand.")
    else:
        print_help(context, handle_miner)


@handle_miner.subcommand("look")
def handle_miner_look(context: DeviceContext, _):
    """
    View miner configuration
    """

    service: Service = context.get_service("miner")
    if service is None:
        print("You have to create the miner service before you can use it.")
        return

    miner: Miner = context.get_client().get_miner(service.uuid)

    print("Destination wallet: " + miner.wallet)
    print("Running: " + ["no", "yes"][service.running])
    print(f"Power: {miner.power * 100}%")
    if service.running:
        print(f"Mining speed: {service.speed} MC/s")


@handle_miner.subcommand("power")
def handle_miner_power(context: DeviceContext, args: List[str]):
    """
    Change miner power
    """

    if len(args) != 1:
        print("usage: miner power <percentage>")
        return

    service: Service = context.get_service("miner")
    if service is None:
        print("You have to create the miner service before you can use it.")
        return

    try:
        power: float = float(args[0]) / 100
        if not 0 <= power <= 1:
            raise ValueError
    except ValueError:
        print("percentage has to be an integer between 0 and 100")
        return

    try:
        context.get_client().miner_power(service.uuid, power)
    except WalletNotFoundException:
        print("Wallet does not exist.")


@handle_miner.subcommand("wallet")
def handle_miner_wallet(context: DeviceContext, args: List[str]):
    """
    Connect the miner to a different wallet
    """

    if len(args) != 1:
        print("usage: miner wallet <uuid>")
        return

    service: Service = context.get_service("miner")
    if service is None:
        print("You have to create the miner service before you can use it.")
        return

    if not is_uuid(args[0]):
        print("Invalid wallet uuid")
        return

    try:
        context.get_client().miner_wallet(service.uuid, args[0])
    except WalletNotFoundException:
        print("Wallet does not exist.")
