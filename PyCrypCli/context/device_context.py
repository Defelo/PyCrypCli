import readline

from .context import Context
from .main_context import MainContext
from .root_context import RootContext
from ..exceptions import InvalidWalletFileError
from ..models import Device, File, Service, PublicService
from ..util import extract_wallet


class DeviceContext(MainContext):
    def __init__(self, root_context: RootContext, session_token: str, device: Device):
        super().__init__(root_context, session_token)

        self.host: Device = device
        self.pwd: File = self.get_root_dir()
        self.last_portscan: tuple[str, list[PublicService]] | None = None

    def update_pwd(self) -> None:
        if self.pwd.uuid:
            self.pwd = self.host.get_file(self.pwd.uuid)

    def is_localhost(self) -> bool:
        return self.user_uuid == self.host.owner_uuid

    @property
    def prompt(self) -> str:
        self.update_pwd()
        if self.is_localhost():
            color = "\033[38;2;100;221;23m"
        else:
            color = "\033[38;2;255;64;23m"
        return f"{color}[{self.username}@{self.host.name}:{self.file_to_path(self.pwd)}]$\033[0m "

    def loop_tick(self) -> None:
        super().loop_tick()

        self.host.update()
        self.check_device_permission()

    def check_device_permission(self) -> bool:
        if self.host.owner_uuid != self.user_uuid and all(
            service.device_uuid != self.host.uuid for service in Service.list_part_owner(self.client)
        ):
            print("You don't have access to this device anymore.")
            self.close()
            return False

        return True

    def check_powered_on(self) -> bool:
        if not self.host.powered_on:
            print("This device is not powered on.")
            self.close()
            return False

        return True

    def before_command(self) -> bool:
        return self.check_device_permission() and self.check_powered_on()

    def enter_context(self) -> None:
        Context.enter_context(self)

    def leave_context(self) -> None:
        pass

    def reenter_context(self) -> None:
        Context.reenter_context(self)

    def get_files(self, parent_dir_uuid: str | None) -> list[File]:
        return self.host.get_files(parent_dir_uuid)

    def get_parent_dir(self, file: File) -> File:
        if file.parent_dir_uuid is None:
            return self.get_root_dir()
        return self.host.get_file(file.parent_dir_uuid)

    def get_root_dir(self) -> File:
        return File.get_root_directory(self.client, self.host.uuid)

    def get_file(self, filename: str, directory_uuid: str | None) -> File | None:
        files: list[File] = self.get_files(directory_uuid)
        for file in files:
            if file.name == filename:
                return file
        return None

    def get_filenames(self, directory: str) -> list[str]:
        return [file.name for file in self.get_files(directory)]

    def get_wallet_credentials_from_file(self, filepath: str) -> tuple[str, str]:
        file: File | None = self.path_to_file(filepath)
        if file is None:
            raise FileNotFoundError

        wallet: tuple[str, str] | None = extract_wallet(file.content)
        if wallet is None:
            raise InvalidWalletFileError

        return wallet

    def file_path_completer(self, path: str, dirs_only: bool = False) -> list[str]:
        base_path: str = "/".join(path.split("/")[:-1])
        if path.startswith("/"):
            base_path = "/" + base_path
        base_dir: File | None = self.path_to_file(base_path)
        if base_dir is None or not base_dir.is_directory:
            return []
        if base_path:
            readline.set_completer_delims("/")
        return [
            file.name + "/\0" * file.is_directory
            for file in self.get_files(base_dir.uuid)
            if file.is_directory or not dirs_only
        ] + ["./\0", "../\0"] * path.split("/")[-1].startswith(".")

    def path_to_file(self, path: str) -> File | None:
        pwd: File = self.get_root_dir() if path.startswith("/") else self.pwd
        for file_name in path.split("/"):
            if not file_name or file_name == ".":
                continue
            if file_name == "..":
                pwd = self.get_parent_dir(pwd)
            else:
                if not (file := self.get_file(file_name, pwd.uuid)):
                    return None
                pwd = file
        return pwd

    def file_to_path(self, file: File) -> str:
        if file.is_root_directory:
            return "/"

        path: list[File] = [file]
        while path[-1].parent_dir_uuid is not None:
            path.append(self.host.get_file(path[-1].parent_dir_uuid))
        return "/" + "/".join(f.name for f in path[::-1])
