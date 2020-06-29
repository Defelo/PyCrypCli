import re
import time
from typing import List

from PyCrypCli.commands.command import command
from PyCrypCli.commands.files import create_file
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import Wallet, Transaction
from PyCrypCli.util import is_uuid, extract_wallet, strip_float


@command("morphcoin", [DeviceContext])
def handle_morphcoin(context: DeviceContext, args: List[str]):
    """
    Manage your Morphcoin wallet
    """

    if args:
        print("Unknown subcommand.")
    else:
        print_help(context, handle_morphcoin)


@handle_morphcoin.subcommand("create")
def handle_morphcoin_create(context: DeviceContext, args: List[str]):
    """
    Create a new MorphCoin wallet
    """

    if len(args) != 1:
        print("usage: morphcoin create <filepath>")
        return

    filepath: str = args[0]
    if context.path_to_file(filepath) is not None:
        print(f"A file with the name '{filepath}' already exists.")
        return

    try:
        wallet: Wallet = context.get_client().create_wallet()
        if not create_file(context, filepath, wallet.uuid + " " + wallet.key):
            context.get_client().delete_wallet(wallet)
    except AlreadyOwnAWalletException:
        print("You already own a wallet")


@handle_morphcoin.subcommand("list")
def handle_morphcoin_list(context: DeviceContext, _):
    """
    List your MorphCoin wallets
    """

    wallets = context.get_client().list_wallets()
    if not wallets:
        print("You don't own any wallet.")
    else:
        print("Your wallets:")
    for wallet in wallets:
        print(f" - {wallet}")


@handle_morphcoin.subcommand("look")
def handle_morphcoin_look(context: DeviceContext, args: List[str]):
    """
    View the balance of your wallet
    """

    if len(args) != 1:
        print("usage: morphcoin look <filepath>")
        return

    try:
        wallet: Wallet = context.get_wallet_from_file(args[0])
    except FileNotFoundException:
        print("File does not exist.")
        return
    except InvalidWalletFile:
        print("File is no wallet file.")
        return
    except UnknownSourceOrDestinationException:
        print("Invalid wallet file. Wallet does not exist.")
        return
    except PermissionDeniedException:
        print("Invalid wallet file. Key is incorrect.")
        return

    print(f"UUID: {wallet.uuid}")
    print(f"Balance: {strip_float(wallet.amount / 1000, 3)} morphcoin")


@handle_morphcoin.subcommand("transactions")
def handle_morphcoin_transactions(context: DeviceContext, args: List[str]):
    """
    View the transaction history of your wallet
    """

    if len(args) != 1:
        print("usage: morphcoin transactions <filepath>")
        return

    try:
        wallet: Wallet = context.get_wallet_from_file(args[0])
    except FileNotFoundException:
        print("File does not exist.")
        return
    except InvalidWalletFile:
        print("File is no wallet file.")
        return
    except UnknownSourceOrDestinationException:
        print("Invalid wallet file. Wallet does not exist.")
        return
    except PermissionDeniedException:
        print("Invalid wallet file. Key is incorrect.")
        return

    transactions: List[Transaction] = context.get_client().get_transactions(wallet, wallet.transactions, 0)

    if not transactions:
        print("No transactions found for this wallet.")
    else:
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
        text = f"{transaction.time_stamp.ctime()}| {strip_float(amount / 1000, 3)} MC: {source} -> {destination}"
        if usage:
            text += f" (Usage: {usage})"
        print(text)


@handle_morphcoin.subcommand("reset")
def handle_morphcoin_reset(context: DeviceContext, args: List[str]):
    """
    Reset your wallet in case you lost the secret key
    """

    if len(args) != 1:
        print("usage: morphcoin reset <uuid>")
        return

    wallet_uuid = args[0]
    if not is_uuid(wallet_uuid):
        print("Invalid wallet uuid.")
        return

    try:
        context.get_client().reset_wallet(wallet_uuid)
    except UnknownSourceOrDestinationException:
        print("Wallet does not exist.")
    except PermissionDeniedException:
        print("Permission denied.")


@handle_morphcoin.subcommand("watch")
def handle_morphcoin_watch(context: DeviceContext, args: List[str]):
    """
    Live view of the wallet balance
    """

    if len(args) != 1:
        print("usage: morphcoin watch <filepath>")
        return

    try:
        wallet: Wallet = context.get_wallet_from_file(args[0])
    except FileNotFoundException:
        print("File does not exist.")
        return
    except InvalidWalletFile:
        print("File is no wallet file.")
        return
    except UnknownSourceOrDestinationException:
        print("Invalid wallet file. Wallet does not exist.")
        return
    except PermissionDeniedException:
        print("Invalid wallet file. Key is incorrect.")
        return

    current_mining_rate: float = 0
    last_update: float = 0

    print(f"UUID: {wallet.uuid}")
    try:
        while True:
            now = time.time()

            if now - last_update > 20:
                try:
                    wallet: Wallet = context.get_client().get_wallet(wallet.uuid, wallet.key)
                except UnknownSourceOrDestinationException:
                    print("Invalid wallet file. Wallet does not exist.")
                    return
                except PermissionDeniedException:
                    print("Invalid wallet file. Key is incorrect.")
                    return

                current_mining_rate: float = 0
                for _, service in context.get_client().get_miners(wallet.uuid):
                    if service.running:
                        current_mining_rate += service.speed

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


@handle_morphcoin_create.completer()
def morphcoin_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0], dirs_only=True)


@command("pay", [DeviceContext])
def handle_pay(context: DeviceContext, args: List[str]):
    """
    Send Morphcoins to another wallet
    """

    if len(args) < 3:
        print("usage: pay <filename> <receiver> <amount> [usage]")
        print("   or: pay <uuid> <key> <receiver> <amount> [usage]")
        return

    try:
        if extract_wallet(f"{args[0]} {args[1]}") is not None:
            wallet: Wallet = context.get_client().get_wallet(args[0], args[1])
            args.pop(0)
        else:
            wallet: Wallet = context.get_wallet_from_file(args[0])
    except FileNotFoundException:
        print("File does not exist.")
        return
    except InvalidWalletFile:
        print("File is no wallet file.")
        return
    except UnknownSourceOrDestinationException:
        print("Invalid wallet file. Wallet does not exist.")
        return
    except PermissionDeniedException:
        print("Invalid wallet file. Key is incorrect.")
        return

    receiver: str = args[1]
    if not is_uuid(receiver):
        print("Invalid receiver.")
        return

    if not re.match(r"^\d+(\.\d+)?$", args[2]) or round(float(args[2]) * 1000) <= 0:
        print("amount is not a valid number.")
        return

    amount: int = round(float(args[2]) * 1000)
    if amount < 1:
        print("amount is not a positive number.")
        return
    elif amount > wallet.amount:
        print("Not enough coins. Transaction cancelled.")
        return

    try:
        context.get_client().send(wallet, receiver, amount, " ".join(args[3:]))
        print(f"Sent {strip_float(amount / 1000, 3)} morphcoin to {receiver}.")
    except UnknownSourceOrDestinationException:
        print("Destination wallet does not exist.")


@handle_pay.completer()
def pay_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0])
