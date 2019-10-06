from typing import List

from ..commands.command import command, CTX_DEVICE
from ..exceptions import *
from ..game import Game
from ..game_objects import Wallet, Transaction
from ..util import is_uuid


@command(["morphcoin"], CTX_DEVICE, "Manage your Morphcoin wallet")
def handle_morphcoin(game: Game, _, args: List[str]):
    if not ((len(args) == 2 and args[0] in ("create", "look", "transactions", "reset")) or (args == ["list"])):
        print("usage: morphcoin create|list|look|transactions [<filename>]")
        print("       morphcoin reset <uuid>")
        return

    if args[0] == "create":
        filename: str = args[1]
        if game.get_file(filename) is not None:
            print(f"A file with the name '{filename}' already exists.")
            return

        try:
            wallet: Wallet = game.client.create_wallet()
            game.client.create_file(game.get_device().uuid, filename, wallet.uuid + " " + wallet.key)
        except AlreadyOwnAWalletException:
            print("You already own a wallet")
    elif args[0] == "list":
        wallets = game.client.list_wallets()
        if not wallets:
            print("You don't own any wallet.")
        else:
            print("Your wallets:")
        for wallet in wallets:
            print(f" - {wallet}")
    elif args[0] == "look":
        filename: str = args[1]
        try:
            wallet: Wallet = game.get_wallet_from_file(filename)
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
        print(f"Balance: {wallet.amount} morphcoin")
    elif args[0] == "transactions":
        filename: str = args[1]
        try:
            wallet: Wallet = game.get_wallet_from_file(filename)
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

        transactions: List[Transaction] = wallet.transactions

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
            text = f"{transaction.time_stamp.ctime()}| {amount} MC: {source} -> {destination}"
            if usage:
                text += f" (Usage: {usage})"
            print(text)
    elif args[0] == "reset":
        wallet_uuid = args[1]
        if not is_uuid(wallet_uuid):
            print("Invalid wallet uuid.")
            return

        try:
            game.client.reset_wallet(wallet_uuid)
        except UnknownSourceOrDestinationException:
            print("Wallet does not exist.")
        except PermissionDeniedException:
            print("Permission denied.")


@command(["pay"], CTX_DEVICE, "Send Morphcoins to another wallet")
def handle_pay(game: Game, _, args: List[str]):
    if len(args) < 3:
        print("usage: pay <filename> <receiver> <amount> [usage]")
        return

    filename: str = args[0]
    try:
        wallet: Wallet = game.get_wallet_from_file(filename)
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

    if not args[2].isnumeric():
        print("amount is not a number.")
        return

    amount: int = int(args[2])
    if amount > wallet.amount:
        print("Not enough coins. Transaction cancelled.")
        return

    try:
        game.client.send(wallet, receiver, amount, " ".join(args[3:]))
        print(f"Sent {amount} morphcoin to {receiver}.")
    except UnknownSourceOrDestinationException:
        print("Destination wallet does not exist.")
