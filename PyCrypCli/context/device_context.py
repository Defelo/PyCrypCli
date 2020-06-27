from typing import Optional, Tuple, List

import readline

from PyCrypCli.context.context import Context
from PyCrypCli.context.main_context import MainContext
from PyCrypCli.context.root_context import RootContext
from PyCrypCli.exceptions import FileNotFoundException
from PyCrypCli.game_objects import Device, File, Service, Wallet


class DeviceContext(MainContext):
    def __init__(self, root_context: RootContext, session_token: str, device: Device):
        super().__init__(root_context, session_token)

        self.host: Device = device
        self.pwd: File = self.get_root_dir()
        self.last_portscan: Optional[Tuple[str, List[Service]]] = None

    def update_pwd(self):
        if self.pwd.uuid is not None:
            self.pwd = self.get_client().get_file(self.host.uuid, self.pwd.uuid)

    def is_localhost(self):
        return self.user_uuid == self.host.owner

    def get_prompt(self) -> str:
        self.update_pwd()
        if self.is_localhost():
            color: str = "\033[38;2;100;221;23m"
        else:
            color: str = "\033[38;2;255;64;23m"
        return f"{color}[{self.username}@{self.host.name}:{self.file_to_path(self.pwd)}]$\033[0m "

    def loop_tick(self):
        super().loop_tick()

        self.host: Device = self.root_context.client.device_info(self.host.uuid)
        self.check_device_permission()

    def check_device_permission(self) -> bool:
        if self.host.owner != self.user_uuid and all(
            service.device != self.host.uuid for service in self.get_client().list_part_owner()
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

    def enter_context(self):
        Context.enter_context(self)

    def leave_context(self):
        pass

    def reenter_context(self):
        Context.reenter_context(self)

    def get_files(self, directory: str) -> List[File]:
        return self.get_client().get_files(self.host.uuid, directory)

    def get_parent_dir(self, file: File) -> File:
        if file.parent_dir_uuid is not None:
            return self.get_client().get_file(self.host.uuid, file.parent_dir_uuid)
        else:
            return self.get_root_dir()

    def get_root_dir(self) -> File:
        return File(None, self.host.uuid, None, None, True, None)

    def get_file(self, filename: str, directory: str) -> Optional[File]:
        files: List[File] = self.get_files(directory)
        for file in files:
            if file.filename == filename:
                return file
        return None

    def get_filenames(self, directory: str) -> List[str]:
        return [file.filename for file in self.get_files(directory)]

    def get_wallet_from_file(self, filepath: str) -> Wallet:
        file: File = self.path_to_file(filepath)
        if file is None:
            raise FileNotFoundException

        return self.extract_wallet(file.content)

    def get_last_portscan(self) -> Tuple[str, List[Service]]:
        return self.last_portscan

    def update_last_portscan(self, scan: Tuple[str, List[Service]]):
        self.last_portscan: Tuple[str, List[Service]] = scan

    def get_service(self, name: str) -> Optional[Service]:
        services: List[Service] = self.get_client().get_services(self.host.uuid)
        for service in services:
            if service.name == name:
                return service
        return None

    def file_path_completer(self, path: str, dirs_only: bool = False) -> List[str]:
        base_path: str = "/".join(path.split("/")[:-1])
        if path.startswith("/"):
            base_path: str = "/" + base_path
        base_dir: Optional[File] = self.path_to_file(base_path)
        if base_dir is None or not base_dir.is_directory:
            return []
        if base_path:
            readline.set_completer_delims("/")
        return [
            file.filename + "/\0" * file.is_directory
            for file in self.get_files(base_dir.uuid)
            if file.is_directory or not dirs_only
        ] + ["./\0", "../\0"] * path.split("/")[-1].startswith(".")

    def path_to_file(self, path: str) -> Optional[File]:
        pwd: File = self.get_root_dir() if path.startswith("/") else self.pwd
        for file_name in path.split("/"):
            if not file_name or file_name == ".":
                continue
            elif file_name == "..":
                pwd = self.get_parent_dir(pwd)
            else:
                pwd: Optional[File] = self.get_file(file_name, pwd.uuid)
                if pwd is None:
                    return None
        return pwd

    def file_to_path(self, file: Optional[File]) -> str:
        if file.uuid is None:
            return "/"
        path: List[File] = [file]
        while path[-1].parent_dir_uuid is not None:
            path.append(self.get_client().get_file(self.host.uuid, path[-1].parent_dir_uuid))
        return "/" + "/".join(f.filename for f in path[::-1])
