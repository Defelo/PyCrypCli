from typing import List

from PyCrypCli.exceptions import ServiceNotFoundException, WalletNotFoundException

from PyCrypCli.commands import CommandError, command
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import DeviceContext
from PyCrypCli.game_objects import Miner
from PyCrypCli.util import is_uuid


def get_miner(context: DeviceContext) -> Miner:
    try:
        return context.host.get_miner()
    except ServiceNotFoundException:
        raise CommandError("You have to create the miner service before you can use it.")


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

    miner: Miner = get_miner(context)
    print("Destination wallet: " + miner.wallet)
    print("Running: " + ["no", "yes"][miner.running])
    print(f"Power: {miner.power * 100}%")
    if miner.running:
        print(f"Mining speed: {miner.speed} MC/s")


@handle_miner.subcommand("power")
def handle_miner_power(context: DeviceContext, args: List[str]):
    """
    Change miner power
    """

    if len(args) != 1:
        raise CommandError("usage: miner power <percentage>")

    miner: Miner = get_miner(context)

    try:
        power: float = float(args[0]) / 100
        if not 0 <= power <= 1:
            raise ValueError
    except ValueError:
        raise CommandError("percentage has to be an integer between 0 and 100")

    try:
        miner.set_power(power)
    except WalletNotFoundException:
        raise CommandError("Wallet does not exist.")


@handle_miner.subcommand("wallet")
def handle_miner_wallet(context: DeviceContext, args: List[str]):
    """
    Connect the miner to a different wallet
    """

    if len(args) != 1:
        raise CommandError("usage: miner wallet <uuid>")

    miner: Miner = get_miner(context)

    if not is_uuid(args[0]):
        raise CommandError("Invalid wallet uuid")

    try:
        miner.set_wallet(args[0])
    except WalletNotFoundException:
        raise CommandError("Wallet does not exist.")
