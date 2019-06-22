from typing import List, Tuple

from commands.command import command
from exceptions import *
from game import Game
from util import extract_wallet


@command(["ls", "l", "dir"], "List all files")
def handle_ls(game: Game, *_):
    files: List[dict] = game.client.get_files(game.device_uuid)
    for file in files:
        print(file["filename"])


@command(["touch"], "Create a new file with given content")
def handle_touch(game: Game, args: List[str]):
    if not args:
        print("usage: touch <filename> [content]")
        return

    filename, *content = args
    content: str = " ".join(content)

    if not filename:
        print("Filename cannot be empty.")
    if len(filename) > 64:
        print("Filename cannot be longer than 64 characters.")

    if game.get_file(filename) is not None:
        print(f"File `{filename}` already exists.")
        handle_rm(game, [filename])

    if game.get_file(filename) is None:
        game.client.create_file(game.device_uuid, filename, content)


@command(["cat"], "Print the content of a file")
def handle_cat(game: Game, args: List[str]):
    if not args:
        print("usage: cat <filename>")
        return

    filename: str = args[0]
    file: dict = game.get_file(filename)
    if file is None:
        print("File does not exist.")
        return

    print(file["content"])


@command(["rm"], "Remove a file")
def handle_rm(game: Game, args: List[str]):
    if not args:
        print("usage: rm <filename>")
        return

    filename: str = args[0]
    file: dict = game.get_file(filename)
    if file is None:
        print("File does not exist.")
        return

    if game.ask(f"Are you sure you want to delete `{filename}`? [yes|no] ", ["yes", "no"]) == "no":
        print("File has not been deleted.")
        return

    content: str = file["content"]
    wallet: Tuple[str, str] = extract_wallet(content)
    if wallet is not None:
        wallet_uuid, wallet_key = wallet
        try:
            amount: int = game.client.get_wallet(wallet_uuid, wallet_key)["amount"]
            choice: str = game.ask(
                f"\033[38;2;255;51;51mThis file contains {amount} morphcoin. "
                f"Do you want to delete the corresponding wallet? [yes|no] \033[0m",
                ["yes", "no"]
            )
            if choice == "yes":
                game.client.delete_wallet(wallet_uuid, wallet_key)
                print("The wallet has been deleted.")
            else:
                print("The following key might now be the only way to access your wallet.")
                print("Note that you can't create another wallet without this key.")
                print(content)
        except UnknownSourceOrDestinationException:
            pass
        except PermissionDeniedException:
            pass
    game.client.remove_file(game.device_uuid, file["uuid"])


@command(["cp"], "Create a copy of a file")
def handle_cp(game: Game, args: List[str]):
    if len(args) != 2:
        print("usage: cp <source> <destination>")
        return

    source: str = args[0]
    destination: str = args[1]

    if not destination:
        print("Destination filename cannot be empty.")
    if len(destination) > 64:
        print("Destination filename cannot be longer than 64 characters.")

    file: dict = game.get_file(source)
    if file is None:
        print("File does not exist.")
        return

    if game.get_file(destination) is not None:
        print(f"File `{destination}` already exists.")
        handle_rm(game, [destination])

    if game.get_file(destination) is None:
        game.client.create_file(game.device_uuid, destination, file["content"])


@command(["mv"], "Rename a file")
def handle_mv(game: Game, args: List[str]):
    if len(args) != 2:
        print("usage: mv <source> <destination>")
        return

    source: str = args[0]
    destination: str = args[1]

    if not destination:
        print("Destination filename cannot be empty.")
    if len(destination) > 64:
        print("Destination filename cannot be longer than 64 characters.")

    file: dict = game.get_file(source)
    if file is None:
        print("File does not exist.")
        return

    if game.get_file(destination) is not None:
        print(f"File `{destination}` already exists.")
        handle_rm(game, [destination])

    if game.get_file(destination) is None:
        game.client.create_file(game.device_uuid, destination, file["content"])
        game.client.remove_file(game.device_uuid, file["uuid"])
