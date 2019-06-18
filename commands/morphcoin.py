from typing import List, Tuple

from commands.command import command
from exceptions import *
from game import Game
from util import extract_wallet, is_uuid


@command(["morphcoin"], "Manage your Morphcoin wallet")
def handle_morphcoin(game: Game, args: List[str]):
    if len(args) != 2 or args[0] not in ("create", "look", "list"):
        print("usage: morphcoin create|look|list <filename>")
        return

    filename: str = args[1]
    if args[0] == "create":
        try:
            uuid, key = game.client.create_wallet()
            game.client.create_file(game.device_uuid, filename, uuid + " " + key)
        except AlreadyOwnAWalletException:
            print("You already own a wallet")
    elif args[0] == "look":
        file: dict = game.get_file(filename)
        if file is None:
            print("File does not exist.")
            return

        wallet: Tuple[str, str] = extract_wallet(file["content"])
        if wallet is None:
            print("File is no wallet file.")
            return

        try:
            amount: int = game.client.get_wallet(*wallet)["amount"]
        except SourceOrDestinationInvalidException:
            print("Invalid wallet file. Wallet does not exist.")
            return
        except PermissionDeniedException:
            print("Invalid wallet file. Key is incorrect.")
            return

        print(f"UUID: {wallet[0]}")
        print(f"Balance: {amount} morphcoin")
    elif args[0] == "list":
        file: dict = game.get_file(filename)
        if file is None:
            print("File does not exist.")
            return

        wallet: Tuple[str, str] = extract_wallet(file["content"])
        if wallet is None:
            print("File is no wallet file.")
            return

        try:
            transactions: List[dict] = game.client.get_wallet(*wallet)["transactions"]
        except SourceOrDestinationInvalidException:
            print("Invalid wallet file. Wallet does not exist.")
            return
        except PermissionDeniedException:
            print("Invalid wallet file. Key is incorrect.")
            return

        for transaction in transactions:
            source: str = transaction["source_uuid"]
            if source == wallet[0]:
                source: str = "self"
            destination: str = transaction["destination_uuid"]
            if destination == wallet[0]:
                destination: str = "self"
            amount: int = transaction["send_amount"]
            time_stamp: str = transaction["time_stamp"]
            usage: str = transaction["usage"]
            text = f"{time_stamp}: {amount} morphcoin ({source} -> {destination})"
            if usage:
                text += f" (Usage: {usage})"
            print(text)


@command(["pay"], "Send Morphcoins to another wallet")
def handle_pay(game: Game, args: List[str]):
    if len(args) < 3:
        print("usage: pay <filename> <receiver> <amount> [usage]")
        return

    file: dict = game.get_file(args[0])
    if file is None:
        print("File does not exist.")
        return

    wallet: Tuple[str, str] = extract_wallet(file["content"])
    if wallet is None:
        print("File is no wallet file.")
        return

    wallet_uuid, wallet_key = wallet
    receiver: str = args[1]
    if not is_uuid(receiver):
        print("Invalid receiver.")
        return

    if not args[2].isnumeric():
        print("amount is not a number.")
        return

    amount: int = int(args[2])
    try:
        game.client.get_wallet(wallet_uuid, wallet_key)
    except SourceOrDestinationInvalidException:
        print("Invalid wallet file. Wallet does not exist.")
        return
    except PermissionDeniedException:
        print("Invalid wallet file. Key is incorrect.")
        return

    try:
        game.client.send(wallet_uuid, wallet_key, receiver, amount, " ".join(args[3:]))
        print(f"Sent {amount} morphcoin to {receiver}.")
    except PermissionDeniedException:
        print("Invalid wallet file. Key is incorrect.")
    except NotEnoughCoinsException:
        print("Not enough coins. Transaction canceled.")
    except SourceOrDestinationInvalidException:
        print("Destination wallet does not exist.")
