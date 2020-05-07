import time
from typing import Optional, Tuple, List

from PyCrypCli.context.context import Context
from PyCrypCli.context.login_context import LoginContext
from PyCrypCli.context.root_context import RootContext
from PyCrypCli.exceptions import InvalidWalletFile
from PyCrypCli.game_objects import Wallet, Device
from PyCrypCli.util import extract_wallet


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
