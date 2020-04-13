from typing import List, Optional, Tuple

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import File, Wallet


@command(["ls", "l", "dir"], [DeviceContext], "List all files")
def handle_ls(context: DeviceContext, args: List[str]):
    if not args:
        directory: File = context.pwd
    else:
        directory: File = context.path_to_file(args[0])
        if directory is None:
            print("No such file or directory.")
            return

    if directory.is_directory:
        files: List[File] = context.get_files(directory.uuid)
        files.sort(key=lambda f: [1 - f.is_directory, f.filename])
    else:
        files: List[File] = [directory]

    for file in files:
        print(["[FILE] ", "[DIR]  "][file.is_directory] + file.filename)


@command(["pwd"], [DeviceContext], "Print the current working directory")
def handle_pwd(context: DeviceContext, *_):
    print(context.file_to_path(context.pwd))


@command(["mkdir"], [DeviceContext], "Create a new directory")
def handle_mkdir(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: mkdir <dirname>")
        return

    *path, dirname = args[0].split("/")
    parent: Optional[File] = context.path_to_file("/".join(path))
    if parent is None:
        print("No such file or directory.")
        return
    elif not parent.is_directory:
        print("That is no directory.")
        return

    try:
        context.get_client().create_file(context.host.uuid, dirname, "", True, parent.uuid)
    except FileAlreadyExistsException:
        print("There already exists a file with this name.")


@command(["cd"], [DeviceContext], "Change the current working directory")
def handle_cd(context: DeviceContext, args: List[str]):
    if not args:
        context.pwd = context.get_root_dir()
    else:
        directory: Optional[File] = context.path_to_file(args[0])
        if directory is None:
            print("The specified directory does not exist")
            return
        elif not directory.is_directory:
            print("That is no directory.")
            return

        context.pwd = directory


def create_file(context: DeviceContext, filepath: str, content: str) -> bool:
    *path, filename = filepath.split("/")
    parent: Optional[File] = context.path_to_file("/".join(path))

    if not filename:
        print("Filename cannot be empty.")
        return False
    elif len(filename) > 64:
        print("Filename cannot be longer than 64 characters.")
        return False

    file: File = context.get_file(filename, parent.uuid)
    if file is not None:
        if file.is_directory:
            print("A directory with this name already exists.")
            return False
        else:
            context.get_client().file_update(file.device, file.uuid, content)
    else:
        context.get_client().create_file(context.host.uuid, filename, content, False, parent.uuid)
    return True


@command(["touch"], [DeviceContext], "Create a new file with given content")
def handle_touch(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: touch <filepath> [content]")
        return

    filepath, *content = args
    create_file(context, filepath, " ".join(content))


@command(["cat"], [DeviceContext], "Print the content of a file")
def handle_cat(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: cat <filepath>")
        return

    path: str = args[0]
    file: File = context.path_to_file(path)
    if file is None:
        print("File does not exist.")
        return
    elif file.is_directory:
        print(f"'{path}' is a directory.")
        return

    print(file.content)


@command(["rm"], [DeviceContext], "Remove a file")
def handle_rm(context: DeviceContext, args: List[str]):
    if not args:
        print("usage: rm <filepath>")
        return

    filepath: str = args[0]
    file: File = context.path_to_file(filepath)
    if file is None:
        print("File does not exist.")
        return

    if file.is_directory:
        pwd = context.pwd
        while True:
            if pwd.uuid == file.uuid:
                print("Refusing to delete this directory.")
                return
            elif pwd.uuid is None:
                break
            pwd = context.get_parent_dir(pwd)

        question: str = f"Are you sure you want to delete the directory `{filepath}` including all contained files?"
    else:
        question: str = f"Are you sure you want to delete this file `{filepath}`?"
    if context.ask(question + " [yes|no] ", ["yes", "no"]) == "no":
        print("File has not been deleted.")
        return

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

    try:
        context.get_client().remove_file(file.device, file.uuid)
    except FileNotChangeableException:
        print("Some files could not be deleted.")


def check_file_movable(
    context: DeviceContext, source: str, destination: str, move: bool
) -> Optional[Tuple[File, str, str]]:
    file: Optional[File] = context.path_to_file(source)
    if file is None:
        print("File does not exist.")
        return

    dest_file: Optional[File] = context.path_to_file(destination)
    absolute = destination[0] == "/"
    dest_parent_path, _, dest_name = destination[absolute:].rpartition("/")
    dest_parent: Optional[File] = context.path_to_file("/" * absolute + dest_parent_path)

    if file.is_directory:
        if dest_file is None:
            if dest_parent is None:
                print("No such file or directory.")
                return
            elif dest_parent.is_directory:
                dest_dir: str = dest_parent.uuid
            else:
                print("Not a directory.")
                return
        elif dest_file.is_directory:
            sub_file: Optional[File] = context.get_file(dest_name, dest_file.uuid)
            if sub_file is not None:
                if sub_file.is_directory:
                    if context.get_files(sub_file.uuid):
                        print("Directory is not empty.")
                        return
                    else:
                        context.get_client().remove_file(sub_file.device, sub_file.uuid)
                else:
                    print("Directory cannot replace a file.")
                    return
            dest_name: str = file.filename
            dest_dir: str = dest_file.uuid
        else:
            print("Directory cannot replace a file.")
            return
    else:
        if dest_file is None:
            if dest_parent is None:
                print("No such file or directory.")
                return
            elif dest_parent.is_directory:
                dest_dir: str = dest_parent.uuid
            else:
                print("Not a directory.")
                return
        elif dest_file.is_directory:
            sub_file: Optional[File] = context.get_file(dest_name, dest_file.uuid)
            if sub_file is not None:
                if sub_file.is_directory:
                    print("File cannot replace a directory.")
                    return
                else:
                    context.get_client().remove_file(sub_file.device, sub_file.uuid)
            dest_name: str = file.filename
            dest_dir: str = dest_file.uuid
        else:
            context.get_client().remove_file(dest_file.device, dest_file.uuid)
            dest_dir: str = dest_parent.uuid

    if dest_dir == file.parent_dir_uuid and dest_name == file.filename:
        return

    if dest_dir is not None:
        dir_to_check: File = context.get_client().get_file(file.device, dest_dir)
        while True:
            if dir_to_check.uuid == file.uuid:
                print(f"You cannot {['copy', 'move'][move]} a directory into itself.")
                return
            elif dir_to_check.uuid is None:
                break
            dir_to_check = context.get_parent_dir(dir_to_check)

    if not dest_name:
        print("Destination filename cannot be empty.")
        return
    elif len(dest_name) > 64:
        print("Destination filename cannot be longer than 64 characters.")
        return

    return file, dest_name, dest_dir


@command(["cp"], [DeviceContext], "Create a copy of a file")
def handle_cp(context: DeviceContext, args: List[str]):
    if len(args) != 2:
        print("usage: cp <source> <destination>")
        return

    result: Optional[Tuple[File, str, str]] = check_file_movable(context, args[0], args[1], move=False)
    if result is None:
        return

    file, dest_name, dest_dir = result
    queue: List[Tuple[File, str, str]] = [(file, dest_name, dest_dir)]
    while queue:
        file, dest_name, dest_dir = queue.pop(0)
        new_file: File = context.get_client().create_file(
            file.device, dest_name, file.content, file.is_directory, dest_dir
        )
        if file.is_directory:
            for child in context.get_files(file.uuid):
                queue.append((child, child.filename, new_file.uuid))


@command(["mv"], [DeviceContext], "Rename a file")
def handle_mv(context: DeviceContext, args: List[str]):
    if len(args) != 2:
        print("usage: mv <source> <destination>")
        return

    result: Optional[Tuple[File, str, str]] = check_file_movable(context, args[0], args[1], move=True)
    if result is None:
        return

    file, dest_name, dest_dir = result
    context.get_client().file_move(file.device, file.uuid, dest_name, dest_dir)


@completer([handle_ls, handle_cat, handle_touch, handle_rm])
def simple_file_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0])


@completer([handle_cd, handle_mkdir])
def simple_directory_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0], dirs_only=True)


@completer([handle_mv, handle_cp])
def copy_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if 1 <= len(args) <= 2:
        return context.file_path_completer(args[-1])
