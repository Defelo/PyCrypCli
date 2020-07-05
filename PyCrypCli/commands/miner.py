from typing import List, Tuple

from PyCrypCli.commands import CommandError, command
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import Service, Miner
from PyCrypCli.util import is_uuid


def get_miner(context: DeviceContext) -> Tuple[Service, Miner]:
    service: Service = context.get_service("miner")
    if service is None:
        raise CommandError("You have to create the miner service before you can use it.")

    miner: Miner = context.get_client().get_miner(service.uuid)
    return service, miner


@command("miner", [DeviceContext])
def handle_miner(context: DeviceContext, args: List[str]):
    """
    Manager your Morphcoin miners
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_miner)


@handle_miner.subcommand("look")
def handle_miner_look(context: DeviceContext, _):
    """
    View miner configuration
    """

    service, miner = get_miner(context)
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
        raise CommandError("usage: miner power <percentage>")

    service, _ = get_miner(context)

    try:
        power: float = float(args[0]) / 100
        if not 0 <= power <= 1:
            raise ValueError
    except ValueError:
        raise CommandError("percentage has to be an integer between 0 and 100")

    try:
        context.get_client().miner_power(service.uuid, power)
    except WalletNotFoundException:
        raise CommandError("Wallet does not exist.")


@handle_miner.subcommand("wallet")
def handle_miner_wallet(context: DeviceContext, args: List[str]):
    """
    Connect the miner to a different wallet
    """

    if len(args) != 1:
        raise CommandError("usage: miner wallet <uuid>")

    service, _ = get_miner(context)

    if not is_uuid(args[0]):
        raise CommandError("Invalid wallet uuid")

    try:
        context.get_client().miner_wallet(service.uuid, args[0])
    except WalletNotFoundException:
        raise CommandError("Wallet does not exist.")
