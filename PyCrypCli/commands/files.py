from typing import List

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import File, Wallet


@command(["ls", "l", "dir"], [DeviceContext], "List all files")
def handle_ls(context: DeviceContext, *_):
    files: List[File] = context.get_client().get_files(context.host.uuid)
    for file in files:
        print(file.filename)


@command(["touch"], [DeviceContext], "Create a new file with given content")
def handle_touch(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: touch <filename> [content]")
        return

    filename, *content = args
    content: str = " ".join(content)

    if not filename:
        print("Filename cannot be empty.")
    if len(filename) > 64:
        print("Filename cannot be longer than 64 characters.")

    file: File = context.get_file(filename)
    if file is not None:
        context.get_client().file_update(file.device, file.uuid, content)
    else:
        context.get_client().create_file(context.host.uuid, filename, content)


@command(["cat"], [DeviceContext], "Print the content of a file")
def handle_cat(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: cat <filename>")
        return

    filename: str = args[0]
    file: File = context.get_file(filename)
    if file is None:
        print("File does not exist.")
        return

    print(file.content)


def remove_file(context: DeviceContext, file: File):
    content: str = file.content
    try:
        wallet: Wallet = context.extract_wallet(content)
        choice: str = context.ask(
            f"\033[38;2;255;51;51mThis file contains {wallet.amount} morphcoin. "
            f"Do you want to delete the corresponding wallet? [yes|no] \033[0m",
            ["yes", "no"],
        )
        if choice == "yes":
            context.get_client().delete_wallet(wallet)
            print("The wallet has been deleted.")
        else:
            print("The following key might now be the only way to access your wallet.")
            print(content)
    except (InvalidWalletFile, UnknownSourceOrDestinationException, PermissionDeniedException):
        pass

    context.get_client().remove_file(file.device, file.uuid)


@command(["rm"], [DeviceContext], "Remove a file")
def handle_rm(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: rm <filename>|*")
        return

    filename: str = args[0]
    if filename == "*":
        if context.ask(f"Are you sure you want to delete all files? [yes|no] ", ["yes", "no"]) == "no":
            print("Files have not been deleted.")
            return

        files: List[File] = context.get_client().get_files(context.host.uuid)
        for file in files:
            remove_file(context, file)
        print("Files have been deleted.")
        return

    file: File = context.get_file(filename)
    if file is None:
        print("File does not exist.")
        return

    if context.ask(f"Are you sure you want to delete `{filename}`? [yes|no] ", ["yes", "no"]) == "no":
        print("File has not been deleted.")
        return

    remove_file(context, file)


@command(["cp"], [DeviceContext], "Create a copy of a file")
def handle_cp(context: DeviceContext, args: List[str]):
    if len(args) != 2:
        print("usage: cp <source> <destination>")
        return

    source: str = args[0]
    destination: str = args[1]

    if not destination:
        print("Destination filename cannot be empty.")
    if len(destination) > 64:
        print("Destination filename cannot be longer than 64 characters.")

    file: File = context.get_file(source)
    if file is None:
        print("File does not exist.")
        return

    if context.get_file(destination) is not None:
        print(f"The file could not be copied because a file with the name '{destination}' already exists.")
        return

    context.get_client().create_file(file.device, destination, file.content)


@command(["mv"], [DeviceContext], "Rename a file")
def handle_mv(context: DeviceContext, args: List[str]):
    if len(args) != 2:
        print("usage: mv <source> <destination>")
        return

    source: str = args[0]
    destination: str = args[1]

    if not destination:
        print("Destination filename cannot be empty.")
    if len(destination) > 64:
        print("Destination filename cannot be longer than 64 characters.")

    file: File = context.get_file(source)
    if file is None:
        print("File does not exist.")
        return

    try:
        context.get_client().file_move(file.device, file.uuid, destination)
    except FileAlreadyExistsException:
        print(f"The file could not be renamed because a file with the name '{destination}' already exists.")


@completer([handle_cat, handle_touch, handle_rm, handle_cp, handle_mv])
def file_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.get_filenames()
