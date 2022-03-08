import time

from .context import Context
from .root_context import RootContext
from ..exceptions import InvalidSessionTokenError
from ..models import Config


class LoginContext(Context):
    def __init__(self, root_context: RootContext):
        super().__init__(root_context)

    @property
    def prompt(self) -> str:
        return "$ "

    def enter_context(self) -> None:
        self.login_loop_presence()

        try:
            self.load_session()
        except InvalidSessionTokenError:
            self.delete_session()
            print("You are not logged in.")
            print("Type `register` to create a new account or `login` if you already have one.")

    def reenter_context(self) -> None:
        super().reenter_context()
        self.login_loop_presence()

    def load_session(self) -> None:
        from .main_context import MainContext

        config: Config = self.root_context.read_config_file()

        if (server_config := config.servers.get(self.root_context.host)) and server_config.token:
            self.client.session(server_config.token)
            self.open(MainContext(self.root_context, server_config.token))

    def delete_session(self) -> None:
        config: Config = self.root_context.read_config_file()
        if server_config := config.servers.get(self.root_context.host):
            server_config.token = None
        self.root_context.write_config_file(config)

    def login_loop_presence(self) -> None:
        self.update_presence(
            state=f"Server: {self.root_context.host}",
            details="Logging in",
            start=int(time.time()),
            large_image="cryptic",
            large_text="Cryptic",
        )
