from typing import Any, cast

from .command import command, CommandError
from ..context import DeviceContext
from ..exceptions import (
    FileAlreadyExistsError,
    InvalidWalletFileError,
    UnknownSourceOrDestinationError,
    PermissionDeniedError,
    FileNotChangeableError,
)
from ..models import File, Wallet


@command("ls", [DeviceContext], aliases=["l", "dir"])
def handle_ls(context: DeviceContext, args: list[str]) -> None:
    """
    List all files
    """

    directory = context.pwd if not args else context.path_to_file(args[0])
    if directory is None:
        raise CommandError("No such file or directory.")

    if directory.is_directory:
        files: list[File] = context.get_files(directory.uuid)
        files.sort(key=lambda f: [1 - f.is_directory, f.name])
    else:
        files = [directory]

    for file in files:
        print(["[FILE] ", "[DIR]  "][file.is_directory] + file.name)


@command("pwd", [DeviceContext])
def handle_pwd(context: DeviceContext, _: Any) -> None:
    """
    Print the current working directory
    """

    print(context.file_to_path(context.pwd))


@command("mkdir", [DeviceContext])
def handle_mkdir(context: DeviceContext, args: list[str]) -> None:
    """
    Create a new directory
    """

    if not args:
        raise CommandError("usage: mkdir <dirname>")

    *path, dirname = args[0].split("/")
    parent: File | None = context.path_to_file("/".join(path))
    if parent is None:
        raise CommandError("No such file or directory.")
    if not parent.is_directory:
        raise CommandError("That is no directory.")

    try:
        context.host.create_file(dirname, "", True, parent.uuid)
    except FileAlreadyExistsError:
        raise CommandError("There already exists a file with this name.")


@command("cd", [DeviceContext])
def handle_cd(context: DeviceContext, args: list[str]) -> None:
    """
    Change the current working directory
    """

    if not args:
        context.pwd = context.get_root_dir()
    else:
        directory: File | None = context.path_to_file(args[0])
        if directory is None:
            raise CommandError("The specified directory does not exist")
        if not directory.is_directory:
            raise CommandError("That is no directory.")

        context.pwd = directory


@command("..", [DeviceContext])
def handle_dot_dot(context: DeviceContext, _: Any) -> None:
    """
    Go to parent directory
    """

    handle_cd(context, [".."])


def create_file(context: DeviceContext, filepath: str, content: str) -> None:
    *path, filename = filepath.split("/")
    parent: File | None = context.path_to_file("/".join(path))
    if not parent:
        raise CommandError("Parent directory does not exist.")

    if not filename:
        raise CommandError("Filename cannot be empty.")
    if len(filename) > 64:
        raise CommandError("Filename cannot be longer than 64 characters.")

    file: File | None = context.get_file(filename, parent.uuid)
    if file is not None:
        if file.is_directory:
            raise CommandError("A directory with this name already exists.")
        file.edit(content)
    else:
        context.host.create_file(filename, content, False, parent.uuid)


@command("touch", [DeviceContext])
def handle_touch(context: DeviceContext, args: list[str]) -> None:
    """
    Create a new file with given content
    """

    if not args:
        raise CommandError("usage: touch <filepath> [content]")

    filepath, *content = args
    create_file(context, filepath, " ".join(content))


@command("cat", [DeviceContext])
def handle_cat(context: DeviceContext, args: list[str]) -> None:
    """
    Print the content of a file
    """

    if not args:
        raise CommandError("usage: cat <filepath>")

    path: str = args[0]
    file: File | None = context.path_to_file(path)
    if file is None:
        raise CommandError("File does not exist.")
    if file.is_directory:
        raise CommandError(f"'{path}' is a directory.")

    print(file.content)


@command("rm", [DeviceContext])
def handle_rm(context: DeviceContext, args: list[str]) -> None:
    """
    Remove a file
    """

    if not args:
        raise CommandError("usage: rm <filepath>")

    filepath: str = args[0]
    file: File | None = context.path_to_file(filepath)
    if file is None:
        raise CommandError("File does not exist.")

    if file.is_directory:
        pwd = context.pwd
        while True:
            if pwd.uuid == file.uuid:
                raise CommandError("Refusing to delete this directory.")
            if pwd.uuid is None:
                break
            pwd = context.get_parent_dir(pwd)

        question: str = f"Are you sure you want to delete the directory '{filepath}' including all contained files?"
    else:
        question = f"Are you sure you want to delete the file '{filepath}'?"
    if context.ask(question + " [yes|no] ", ["yes", "no"]) == "no":
        raise CommandError("File has not been deleted.")

    content: str = file.content
    try:
        wallet: Wallet = context.extract_wallet(content)
        choice: str = context.ask(
            f"\033[38;2;255;51;51mThis file contains {wallet.amount} morphcoin. "
            f"Do you want to delete the corresponding wallet? [yes|no] \033[0m",
            ["yes", "no"],
        )
        if choice == "yes":
            wallet.delete()
            print("The wallet has been deleted.")
        else:
            print("The following key might now be the only way to access your wallet.")
            print(content)
    except (InvalidWalletFileError, UnknownSourceOrDestinationError, PermissionDeniedError):
        pass

    try:
        file.delete()
    except FileNotChangeableError:
        raise CommandError("Some files could not be deleted.")


def check_file_movable(
    context: DeviceContext, source: str, destination: str, move: bool
) -> tuple[File, str, str | None] | None:
    file: File | None = context.path_to_file(source)
    if file is None:
        raise CommandError("File does not exist.")

    dest_file: File | None = context.path_to_file(destination)
    absolute = destination[0] == "/"
    dest_parent_path, _, dest_name = destination[absolute:].rpartition("/")
    dest_parent: File | None = context.path_to_file("/" * absolute + dest_parent_path)
    dest_dir: str | None

    if file.is_directory:
        if dest_file is None:
            if dest_parent is None:
                raise CommandError("No such file or directory.")
            if not dest_parent.is_directory:
                raise CommandError("Not a directory.")
            dest_dir = dest_parent.uuid
        elif dest_file.is_directory:
            sub_file: File | None = context.get_file(dest_name, dest_file.uuid)
            if sub_file is not None:
                if sub_file.is_directory:
                    if context.get_files(sub_file.uuid):
                        raise CommandError("Directory is not empty.")
                    sub_file.delete()
                else:
                    raise CommandError("Directory cannot replace a file.")
            dest_name = file.name
            dest_dir = dest_file.uuid
        else:
            raise CommandError("Directory cannot replace a file.")
    else:
        if dest_file is None:
            if dest_parent is None:
                raise CommandError("No such file or directory.")
            if not dest_parent.is_directory:
                raise CommandError("Not a directory.")
            dest_dir = dest_parent.uuid
        elif dest_file.is_directory:
            sub_file = context.get_file(dest_name, dest_file.uuid)
            if sub_file is not None:
                if sub_file.is_directory:
                    raise CommandError("File cannot replace a directory.")
                sub_file.delete()
            dest_name = file.name
            dest_dir = dest_file.uuid
        else:
            dest_file.delete()
            dest_dir = cast(File, dest_parent).uuid

    if dest_dir == file.parent_dir_uuid and dest_name == file.name:
        return None

    if dest_dir is not None:
        dir_to_check: File | None = File.get_file(context.client, file.device_uuid, dest_dir)
        while True:
            if not dir_to_check:
                break
            if dir_to_check.uuid == file.uuid:
                raise CommandError(f"You cannot {['copy', 'move'][move]} a directory into itself.")
            dir_to_check = context.get_parent_dir(dir_to_check)

    if not dest_name:
        raise CommandError("Destination filename cannot be empty.")
    if len(dest_name) > 64:
        raise CommandError("Destination filename cannot be longer than 64 characters.")

    return file, dest_name, dest_dir


@command("cp", [DeviceContext])
def handle_cp(context: DeviceContext, args: list[str]) -> None:
    """
    Create a copy of a file
    """

    if len(args) != 2:
        raise CommandError("usage: cp <source> <destination>")

    result: tuple[File, str, str | None] | None = check_file_movable(context, args[0], args[1], move=False)
    if result is None:
        return

    file, dest_name, dest_dir = result
    queue: list[tuple[File, str, str | None]] = [(file, dest_name, dest_dir)]
    while queue:
        file, dest_name, dest_dir = queue.pop(0)
        new_file: File = context.host.create_file(dest_name, file.content, file.is_directory, dest_dir)
        if file.is_directory:
            for child in context.get_files(file.uuid):
                queue.append((child, child.name, cast(str, new_file.uuid)))


@command("mv", [DeviceContext])
def handle_mv(context: DeviceContext, args: list[str]) -> None:
    """
    Rename a file
    """

    if len(args) != 2:
        raise CommandError("usage: mv <source> <destination>")

    result: tuple[File, str, str | None] | None = check_file_movable(context, args[0], args[1], move=True)
    if result is None:
        return

    file, dest_name, dest_dir = result
    file.move(dest_name, dest_dir)


@handle_ls.completer()
@handle_cat.completer()
@handle_touch.completer()
@handle_rm.completer()
def simple_file_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0])
    return []


@handle_cd.completer()
@handle_mkdir.completer()
def simple_directory_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return context.file_path_completer(args[0], dirs_only=True)
    return []


@handle_mv.completer()
@handle_cp.completer()
def copy_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if 1 <= len(args) <= 2:
        return context.file_path_completer(args[-1])
    return []
