from typing import List

from ..commands.command import command, CTX_DEVICE
from ..exceptions import *
from ..game import Game
from ..game_objects import File, Wallet


@command(["ls", "l", "dir"], CTX_DEVICE, "List all files")
def handle_ls(game: Game, *_):
    files: List[File] = game.client.get_files(game.get_device().uuid)
    for file in files:
        print(file.filename)


@command(["touch"], CTX_DEVICE, "Create a new file with given content")
def handle_touch(game: Game, _, args: List[str]):
    if not args:
        print("usage: touch <filename> [content]")
        return

    filename, *content = args
    content: str = " ".join(content)

    if not filename:
        print("Filename cannot be empty.")
    if len(filename) > 64:
        print("Filename cannot be longer than 64 characters.")

    file: File = game.get_file(filename)
    if file is not None:
        game.client.file_update(file.device, file.uuid, content)
    else:
        game.client.create_file(game.get_device().uuid, filename, content)


@command(["cat"], CTX_DEVICE, "Print the content of a file")
def handle_cat(game: Game, _, args: List[str]):
    if not args:
        print("usage: cat <filename>")
        return

    filename: str = args[0]
    file: File = game.get_file(filename)
    if file is None:
        print("File does not exist.")
        return

    print(file.content)


@command(["rm"], CTX_DEVICE, "Remove a file")
def handle_rm(game: Game, _, args: List[str]):
    if not args:
        print("usage: rm <filename>")
        return

    filename: str = args[0]
    file: File = game.get_file(filename)
    if file is None:
        print("File does not exist.")
        return

    if game.ask(f"Are you sure you want to delete `{filename}`? [yes|no] ", ["yes", "no"]) == "no":
        print("File has not been deleted.")
        return

    content: str = file.content
    try:
        wallet: Wallet = game.extract_wallet(content)
        choice: str = game.ask(
            f"\033[38;2;255;51;51mThis file contains {wallet.amount} morphcoin. "
            f"Do you want to delete the corresponding wallet? [yes|no] \033[0m",
            ["yes", "no"],
        )
        if choice == "yes":
            game.client.delete_wallet(wallet)
            print("The wallet has been deleted.")
        else:
            print("The following key might now be the only way to access your wallet.")
            print(content)
    except (InvalidWalletFile, UnknownSourceOrDestinationException, PermissionDeniedException):
        pass

    game.client.remove_file(file.device, file.uuid)


@command(["cp"], CTX_DEVICE, "Create a copy of a file")
def handle_cp(game: Game, _, args: List[str]):
    if len(args) != 2:
        print("usage: cp <source> <destination>")
        return

    source: str = args[0]
    destination: str = args[1]

    if not destination:
        print("Destination filename cannot be empty.")
    if len(destination) > 64:
        print("Destination filename cannot be longer than 64 characters.")

    file: File = game.get_file(source)
    if file is None:
        print("File does not exist.")
        return

    if game.get_file(destination) is not None:
        print(f"The file could not be copied because a file with the name '{destination}' already exists.")
        return

    game.client.create_file(file.device, destination, file.content)


@command(["mv"], CTX_DEVICE, "Rename a file")
def handle_mv(game: Game, _, args: List[str]):
    if len(args) != 2:
        print("usage: mv <source> <destination>")
        return

    source: str = args[0]
    destination: str = args[1]

    if not destination:
        print("Destination filename cannot be empty.")
    if len(destination) > 64:
        print("Destination filename cannot be longer than 64 characters.")

    file: File = game.get_file(source)
    if file is None:
        print("File does not exist.")
        return

    try:
        game.client.file_move(file.device, file.uuid, destination)
    except FileAlreadyExistsException:
        print(f"The file could not be renamed because a file with the name '{destination}' already exists.")
