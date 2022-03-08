import time

from .context import Context
from .login_context import LoginContext
from .root_context import RootContext
from ..exceptions import InvalidWalletFileError, LoggedOutError
from ..models import Wallet, Device, Service, Config, ServerConfig, InfoResponse
from ..util import extract_wallet


class MainContext(LoginContext):
    def __init__(self, root_context: RootContext, session_token: str):
        super().__init__(root_context)

        self.username: str | None = None
        self.user_uuid: str | None = None
        self.session_token: str | None = session_token

    @property
    def prompt(self) -> str:
        return f"\033[38;2;53;160;171m[{self.username}]$\033[0m "

    def update_user_info(self) -> None:
        info: InfoResponse = self.root_context.client.info()
        self.username = info.name
        self.user_uuid = info.uuid

    def loop_tick(self) -> None:
        self.update_user_info()

    def enter_context(self) -> None:
        Context.enter_context(self)

        self.update_user_info()
        self.save_session()

        self.main_loop_presence()

        print(f"Logged in as {self.username}.")

    def leave_context(self) -> None:
        if self.client.logged_in:
            self.client.logout()
        self.delete_session()
        print("Logged out.")

    def reenter_context(self) -> None:
        Context.reenter_context(self)

        self.main_loop_presence()

    def save_session(self) -> None:
        if not self.session_token:
            raise LoggedOutError

        config: Config = self.root_context.read_config_file()
        config.servers[self.root_context.host] = ServerConfig(token=self.session_token)
        self.root_context.write_config_file(config)

    def delete_session(self) -> None:
        super().delete_session()
        self.session_token = None

    def main_loop_presence(self) -> None:
        self.update_presence(
            state=f"Logged in: {self.username}@{self.root_context.host}",
            details="in Cryptic Terminal",
            start=int(time.time()),
            large_image="cryptic",
            large_text="Cryptic",
        )

    def extract_wallet(self, content: str) -> Wallet:
        wallet: tuple[str, str] | None = extract_wallet(content)
        if wallet is None:
            raise InvalidWalletFileError
        return Wallet.get_wallet(self.client, *wallet)

    def get_hacked_devices(self) -> list[Device]:
        return list(
            {Device.get_device(self.client, service.device_uuid) for service in Service.list_part_owner(self.client)}
        )
