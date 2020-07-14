import re
import time
from typing import List

from PyCrypCli.commands import command, CommandError
from PyCrypCli.commands.files import create_file
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import (
    FileNotFoundException,
    InvalidWalletFile,
    UnknownSourceOrDestinationException,
    PermissionDeniedException,
    AlreadyOwnAWalletException,
)
from PyCrypCli.game_objects import Wallet, Transaction, PublicWallet
from PyCrypCli.util import is_uuid, extract_wallet, strip_float


def get_wallet_from_file(context: DeviceContext, path: str) -> Wallet:
    try:
        return get_wallet(context, *context.get_wallet_credentials_from_file(path))
    except FileNotFoundException:
        raise CommandError("File does not exist.")
    except InvalidWalletFile:
        raise CommandError("File is no wallet file.")


def get_wallet(context: DeviceContext, uuid: str, key: str) -> Wallet:
    try:
        return Wallet.get_wallet(context.client, uuid, key)
    except UnknownSourceOrDestinationException:
        raise CommandError("Invalid wallet file. Wallet does not exist.")
    except PermissionDeniedException:
        raise CommandError("Invalid wallet file. Key is incorrect.")


@command("morphcoin", [DeviceContext])
def handle_morphcoin(context: DeviceContext, args: List[str]):
    """
    Manage your Morphcoin wallet
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_morphcoin)


@handle_morphcoin.subcommand("create")
def handle_morphcoin_create(context: DeviceContext, args: List[str]):
    """
    Create a new MorphCoin wallet
    """

    if len(args) != 1:
        raise CommandError("usage: morphcoin create <filepath>")

    filepath: str = args[0]
    if context.path_to_file(filepath) is not None:
        raise CommandError(f"A file with the name '{filepath}' already exists.")

    try:
        wallet: Wallet = Wallet.create_wallet(context.client)
        try:
            create_file(context, filepath, wallet.uuid + " " + wallet.key)
        except CommandError:
            wallet.delete()
            raise
    except AlreadyOwnAWalletException:
        raise CommandError("You already own a wallet")


@handle_morphcoin.subcommand("list")
def handle_morphcoin_list(context: DeviceContext, _):
    """
    List your MorphCoin wallets
    """

    wallets: List[PublicWallet] = PublicWallet.list_wallets(context.client)
    if not wallets:
        print("You don't own any wallet.")
    else:
        print("Your wallets:")
    for wallet in wallets:
        print(f" - {wallet.uuid}")


@handle_morphcoin.subcommand("look")
def handle_morphcoin_look(context: DeviceContext, args: List[str]):
    """
    View the balance of your wallet
    """

    if len(args) != 1:
        raise CommandError("usage: morphcoin look <filepath>")

    wallet: Wallet = get_wallet_from_file(context, args[0])
    print(f"UUID: {wallet.uuid}")
    print(f"Balance: {strip_float(wallet.amount / 1000, 3)} morphcoin")


@handle_morphcoin.subcommand("transactions")
def handle_morphcoin_transactions(context: DeviceContext, args: List[str]):
    """
    View the transaction history of your wallet
    """

    if len(args) != 1:
        raise CommandError("usage: morphcoin transactions <filepath>")

    wallet: Wallet = get_wallet_from_file(context, args[0])

    if not wallet.transactions:
        print("No transactions found for this wallet.")
        return

    transactions: List[Transaction] = wallet.get_transactions(wallet.transactions, 0)
    print("Transactions for this wallet:")
    for transaction in transactions:
        source: str = transaction.source_uuid
        if source == wallet.uuid:
            source: str = "self"
        destination: str = transaction.destination_uuid
        if destination == wallet.uuid:
            destination: str = "self"
        amount: int = transaction.amount
        usage: str = transaction.usage
        text = f"{transaction.timestamp.ctime()}| {strip_float(amount / 1000, 3)} MC: {source} -> {destination}"
        if usage:
            text += f" (Usage: {usage})"
        print(text)


@handle_morphcoin.subcommand("reset")
def handle_morphcoin_reset(context: DeviceContext, args: List[str]):
    """
    Reset your wallet in case you lost the secret key
    """

    if len(args) != 1:
        raise CommandError("usage: morphcoin reset <uuid>")

    wallet_uuid = args[0]
    if not is_uuid(wallet_uuid):
        raise CommandError("Invalid wallet uuid.")

    try:
        PublicWallet.get_public_wallet(context.client, wallet_uuid).reset_wallet()
    except UnknownSourceOrDestinationException:
        raise CommandError("Wallet does not exist.")
    except PermissionDeniedException:
        raise CommandError("Permission denied.")


@handle_morphcoin.subcommand("watch")
def handle_morphcoin_watch(context: DeviceContext, args: List[str]):
    """
    Live view of the wallet balance
    """

    if len(args) != 1:
        raise CommandError("usage: morphcoin watch <filepath>")

    wallet: Wallet = get_wallet_from_file(context, args[0])
    current_mining_rate: float = 0
    last_update: float = 0

    print(f"UUID: {wallet.uuid}")
    try:
        while True:
            now = time.time()

            if now - last_update > 20:
                wallet: Wallet = get_wallet(context, wallet.uuid, wallet.key)
                current_mining_rate: float = 0
                for miner in wallet.get_miners():
                    if miner.running:
                        current_mining_rate += miner.speed

                last_update: float = now

            current_balance: int = wallet.amount + int(current_mining_rate * 1000 * (now - last_update))
            print(
                end=f"\rBalance: {strip_float(current_balance / 1000, 3)} morphcoin "
                f"({current_mining_rate:.2f} MC/s) ",
                flush=False,
            )
            time.sleep(0.1)
    except KeyboardInterrupt:
        print()


@handle_morphcoin_look.completer()
@handle_morphcoin_transactions.completer()
@handle_morphcoin_watch.completer()
def morphcoin_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0])
    return []


@handle_morphcoin_create.completer()
def morphcoin_create_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0], dirs_only=True)
    return []


@command("pay", [DeviceContext])
def handle_pay(context: DeviceContext, args: List[str]):
    """
    Send Morphcoins to another wallet
    """

    if len(args) < 3:
        raise CommandError(
            "usage: pay <filename> <receiver> <amount> [usage]\n" "   or: pay <uuid> <key> <receiver> <amount> [usage]"
        )

    if extract_wallet(f"{args[0]} {args[1]}") is not None:
        wallet: Wallet = get_wallet(context, args[0], args[1])
        args.pop(0)
    else:
        wallet: Wallet = get_wallet_from_file(context, args[0])

    receiver: str = args[1]
    if not is_uuid(receiver):
        raise CommandError("Invalid receiver.")

    if not re.match(r"^\d+(\.\d+)?$", args[2]) or round(float(args[2]) * 1000) <= 0:
        raise CommandError("amount is not a valid number.")

    amount: int = round(float(args[2]) * 1000)
    if amount < 1:
        raise CommandError("amount is not a positive number.")
    if amount > wallet.amount:
        raise CommandError("Not enough coins. Transaction cancelled.")

    try:
        wallet.send(PublicWallet.get_public_wallet(context.client, receiver), amount, " ".join(args[3:]))
        print(f"Sent {strip_float(amount / 1000, 3)} morphcoin to {receiver}.")
    except UnknownSourceOrDestinationException:
        raise CommandError("Destination wallet does not exist.")


@handle_pay.completer()
def pay_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0])
    return []
