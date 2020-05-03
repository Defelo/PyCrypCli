import re
import time
from typing import List

from PyCrypCli import util
from PyCrypCli.commands.command import command, completer
from PyCrypCli.commands.files import create_file
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import Wallet, Transaction
from PyCrypCli.util import is_uuid, DoWaitingHackingThread, extract_wallet, strip_float


@command(["morphcoin"], [DeviceContext], "Manage your Morphcoin wallet")
def handle_morphcoin(context: DeviceContext, args: List[str]):
    if not (
        (len(args) == 2 and args[0] in ("create", "look", "transactions", "reset", "watch"))
        or (args in (["list"], ["search"]))
    ):
        print("usage: morphcoin create|list|look|transactions|watch [<filepath>]")
        print("       morphcoin reset <uuid>")
        return

    if args[0] == "create":
        filepath: str = args[1]
        if context.path_to_file(filepath) is not None:
            print(f"A file with the name '{filepath}' already exists.")
            return

        try:
            wallet: Wallet = context.get_client().create_wallet()
            if not create_file(context, filepath, wallet.uuid + " " + wallet.key):
                context.get_client().delete_wallet(wallet)
        except AlreadyOwnAWalletException:
            print("You already own a wallet")
    elif args[0] == "list":
        wallets = context.get_client().list_wallets()
        if not wallets:
            print("You don't own any wallet.")
        else:
            print("Your wallets:")
        for wallet in wallets:
            print(f" - {wallet}")
    elif args[0] == "look":
        try:
            wallet: Wallet = context.get_wallet_from_file(args[1])
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
    elif args[0] == "transactions":
        try:
            wallet: Wallet = context.get_wallet_from_file(args[1])
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
    elif args[0] == "reset":
        wallet_uuid = args[1]
        if not is_uuid(wallet_uuid):
            print("Invalid wallet uuid.")
            return

        try:
            context.get_client().reset_wallet(wallet_uuid)
        except UnknownSourceOrDestinationException:
            print("Wallet does not exist.")
        except PermissionDeniedException:
            print("Permission denied.")
    elif args[0] == "search":
        started: float = time.time()
        try:
            util.do_waiting_hacking("Initializing", 10)
        except KeyboardInterrupt:
            print()
        if 6.5 < time.time() - started < 7.5:
            print("Initialization successful.")
        else:
            print("Initialization failed.")
            return

        hacking_thread: DoWaitingHackingThread = DoWaitingHackingThread("Hacking")
        hacking_thread.start()

        for file in context.get_client().get_files(context.host.uuid, context.pwd.uuid):
            time.sleep(5)
            try:
                wallet: Wallet = context.get_wallet_from_file(file.filename)
                print(f"\r{file.filename}: {wallet.uuid} {wallet.key} ({wallet.amount} MC)")
            except InvalidWalletFile:
                print(f"\r{file.filename} is no wallet file.")
            except UnknownSourceOrDestinationException:
                print(f"\r{file.filename} contains an invalid wallet uuid.")
            except PermissionDeniedException:
                print(f"\r{file.filename} contains an invalid wallet key.")
            except KeyboardInterrupt:
                hacking_thread.stop()
                return
        hacking_thread.stop()
    elif args[0] == "watch":
        try:
            wallet: Wallet = context.get_wallet_from_file(args[1])
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


@completer([handle_morphcoin])
def morphcoin_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["create", "list", "look", "transactions", "reset", "watch"]
    elif len(args) == 2:
        if args[0] in ("look", "transactions", "watch"):
            return context.file_path_completer(args[1])
        elif args[0] == "create":
            return context.file_path_completer(args[1], dirs_only=True)


@command(["pay"], [DeviceContext], "Send Morphcoins to another wallet")
def handle_pay(context: DeviceContext, args: List[str]):
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


@completer([handle_pay])
def pay_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0])
