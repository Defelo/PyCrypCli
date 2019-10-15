import json
import os
import re
import time
from typing import Optional, List, Dict, Type, Tuple, Callable

import readline
from pypresence import PyPresenceException, InvalidPipe, Presence

from PyCrypCli.client import Client
from PyCrypCli.exceptions import InvalidSessionTokenException, InvalidWalletFile, FileNotFoundException
from PyCrypCli.game_objects import Device, File, Wallet, Service
from PyCrypCli.util import extract_wallet


class RootContext:
    def __init__(
        self,
        server: str,
        config_file: List[str],
        commands: Dict[Type["Context"], Dict[str, Tuple[str, "COMMAND_FUNCTION", "COMPLETER_FUNCTION"]]],
    ):
        self.client: Client = Client(server)
        self.host: str = re.match(r"^wss?://(.+)$", server).group(1).split("/")[0]

        self.config_file: List[str] = config_file

        self.context_stack: List[Context] = []

        self.commands: Dict[Type[Context], Dict[str, Tuple[str, COMMAND_FUNCTION, COMPLETER_FUNCTION]]] = commands

        self.presence: Presence = Presence(client_id="596676243144048640")
        try:
            self.presence.connect()
        except (FileNotFoundError, InvalidPipe):
            self.presence = None

    def open(self, context: "Context"):
        self.context_stack.append(context)
        context.enter_context()

    def close(self):
        self.context_stack.pop().leave_context()
        self.get_context().reenter_context()

    def get_context(self) -> "Context":
        return self.context_stack[-1]

    def get_override_completions(self) -> Optional[List[str]]:
        return self.get_context().override_completions

    def get_commands(self) -> Dict[str, Tuple[str, "COMMAND_FUNCTION", "COMPLETER_FUNCTION"]]:
        return self.commands[type(self.get_context())]

    def read_config_file(self) -> dict:
        for i in range(1, len(self.config_file)):
            path: str = os.path.join(*self.config_file[:i])
            if not os.path.exists(path):
                os.mkdir(path)
        path: str = os.path.join(*self.config_file)
        if not os.path.exists(path):
            self.write_config_file({"servers": {}})
        return json.load(open(path))

    def write_config_file(self, config: dict):
        path: str = os.path.join(*self.config_file)
        with open(path, "w") as file:
            json.dump(config, file)
            file.flush()


class Context:
    def __init__(self, root_context: RootContext):
        self.root_context: RootContext = root_context

        self.override_completions: Optional[List[str]] = None
        self.history: List[str] = []

    def add_to_history(self, command: str):
        if self.history[-1:] != [command]:
            self.history.append(command)

    def get_prompt(self) -> str:
        return "$ "

    def get_client(self) -> Client:
        return self.root_context.client

    def get_commands(self) -> Dict[str, Tuple[str, "COMMAND_FUNCTION", "COMPLETER_FUNCTION"]]:
        return self.root_context.get_commands()

    def ask(self, prompt: str, options: List[str]) -> str:
        while True:
            try:
                choice: str = self.input_no_history(prompt, options).strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEnter one of the following:", ", ".join(options))
                continue
            if choice in options:
                return choice
            print(f"'{choice}' is not one of the following:", ", ".join(options))

    def update_presence(
        self,
        state: str = None,
        details: str = None,
        start: int = None,
        end: int = None,
        large_image: str = None,
        large_text: str = None,
    ):
        if self.root_context.presence is None:
            return
        try:
            self.root_context.presence.update(
                state=state, details=details, start=start, end=end, large_image=large_image, large_text=large_text
            )
        except PyPresenceException:
            pass

    def enter_context(self):
        readline.clear_history()

    def leave_context(self):
        pass

    def reenter_context(self):
        self.restore_history()

    def input_no_history(self, prompt: str, override_completions: Optional[List[str]] = None) -> Optional[str]:
        readline.clear_history()
        old_override: List[str] = self.override_completions
        self.override_completions: List[str] = override_completions or []
        try:
            return input(prompt)
        finally:
            self.restore_history()
            self.override_completions = old_override

    def restore_history(self):
        readline.clear_history()
        for command in self.history:
            readline.add_history(command)

    def open(self, context: "Context"):
        self.root_context.open(context)

    def close(self):
        self.root_context.close()

    def loop_tick(self):
        pass


COMMAND_FUNCTION = Callable[[Context, List[str]], None]
COMPLETER_FUNCTION = Callable[[Context, List[str]], List[str]]


class LoginContext(Context):
    def __init__(self, root_context: RootContext):
        super().__init__(root_context)

    def get_prompt(self) -> str:
        return "$ "

    def enter_context(self):
        self.login_loop_presence()

        try:
            self.load_session()
        except InvalidSessionTokenException:
            self.delete_session()
            print("You are not logged in.")
            print("Type `register` to create a new account or `login` if you already have one.")

    def reenter_context(self):
        super().reenter_context()
        self.login_loop_presence()

    def load_session(self):
        config: dict = self.root_context.read_config_file()

        if "token" in config.setdefault("servers", {}).setdefault(self.root_context.host, {}):
            session_token: str = config["servers"][self.root_context.host]["token"]
            self.get_client().session(session_token)
            self.open(MainContext(self.root_context, session_token))

    def delete_session(self):
        config: dict = self.root_context.read_config_file()
        if "token" in config.setdefault("servers", {}).setdefault(self.root_context.host, {}):
            del config["servers"][self.root_context.host]["token"]
        self.root_context.write_config_file(config)

    def login_loop_presence(self):
        self.update_presence(
            state=f"Server: {self.root_context.host}",
            details="Logging in",
            start=int(time.time()),
            large_image="cryptic",
            large_text="Cryptic",
        )


class MainContext(LoginContext):
    def __init__(self, root_context: RootContext, session_token: str):
        super().__init__(root_context)

        self.username: Optional[str] = None
        self.user_uuid: Optional[str] = None
        self.session_token: Optional[str] = session_token

    def get_prompt(self) -> str:
        return f"\033[38;2;53;160;171m[{self.username}]$\033[0m "

    def update_user_info(self):
        info: dict = self.root_context.client.info()
        self.username: str = info["name"]
        self.user_uuid: str = info["uuid"]

    def loop_tick(self):
        self.update_user_info()

    def enter_context(self):
        Context.enter_context(self)

        self.update_user_info()
        self.save_session()

        self.main_loop_presence()

        print(f"Logged in as {self.username}.")

    def leave_context(self):
        if self.get_client().logged_in:
            self.get_client().logout()
        self.delete_session()
        print("Logged out.")

    def reenter_context(self):
        Context.reenter_context(self)

        self.main_loop_presence()

    def save_session(self):
        config: dict = self.root_context.read_config_file()
        config.setdefault("servers", {}).setdefault(self.root_context.host, {})["token"] = self.session_token
        self.root_context.write_config_file(config)

    def delete_session(self):
        super().delete_session()
        self.session_token = None

    def main_loop_presence(self):
        self.update_presence(
            state=f"Logged in: {self.username}@{self.root_context.host}",
            details="in Cryptic Terminal",
            start=int(time.time()),
            large_image="cryptic",
            large_text="Cryptic",
        )

    def extract_wallet(self, content: str) -> Wallet:
        wallet: Optional[Tuple[str, str]] = extract_wallet(content)
        if wallet is None:
            raise InvalidWalletFile
        return self.get_client().get_wallet(*wallet)

    def get_hacked_devices(self) -> List[Device]:
        return list({self.get_client().device_info(service.device) for service in self.get_client().list_part_owner()})


class DeviceContext(MainContext):
    def __init__(self, root_context: RootContext, session_token: str, device: Device):
        super().__init__(root_context, session_token)

        self.host: Device = device
        self.last_portscan: Optional[Tuple[str, List[Service]]] = None

    def is_localhost(self):
        return self.user_uuid == self.host.owner

    def get_prompt(self) -> str:
        if self.is_localhost():
            return f"\033[38;2;100;221;23m[{self.username}@{self.host.name}]$\033[0m "
        else:
            return f"\033[38;2;255;64;23m[{self.username}@{self.host.name}]$\033[0m "

    def loop_tick(self):
        super().loop_tick()

        self.host: Device = self.root_context.client.device_info(self.host.uuid)

    def enter_context(self):
        Context.enter_context(self)

    def leave_context(self):
        pass

    def reenter_context(self):
        Context.reenter_context(self)

    def get_file(self, filename: str) -> Optional[File]:
        files: List[File] = self.get_client().get_files(self.host.uuid)
        for file in files:
            if file.filename == filename:
                return file
        return None

    def get_filenames(self) -> List[str]:
        return [file.filename for file in self.get_client().get_files(self.host.uuid)]

    def get_wallet_from_file(self, filename: str) -> Wallet:
        file: File = self.get_file(filename)
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
