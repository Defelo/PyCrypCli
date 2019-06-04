from typing import List, Tuple

from commands.command import command
from exceptions import *
from game import Game
from util import extract_wallet, is_uuid


@command(["morphcoin"], "Manage your Morphcoin wallet")
def handle_morphcoin(game: Game, args: List[str]):
    if len(args) != 2 or args[0] not in ("look", "create"):
        print("usage: morphcoin look|create <filename>")
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
        except InvalidWalletException:
            print("Invalid wallet file. Wallet does not exist.")
            return
        except InvalidKeyException:
            print("Invalid wallet file. Key is incorrect.")
            return

        print(f"{amount} morphcoin")


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
    except InvalidWalletException:
        print("Invalid wallet file. Wallet does not exist.")
        return
    except InvalidKeyException:
        print("Invalid wallet file. Key is incorrect.")
        return

    try:
        game.client.send(wallet_uuid, wallet_key, receiver, amount, " ".join(args[3:]))
        print(f"Sent {amount} morphcoin to {receiver}.")
    except SourceWalletTransactionDebtException:
        print("The source wallet would make debt. Transaction canceled.")
    except InvalidWalletException:
        print("Destination wallet does not exist.")
