import time

from PyCrypCli.context.context import Context
from PyCrypCli.context.root_context import RootContext
from PyCrypCli.exceptions import InvalidSessionTokenException


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
        from PyCrypCli.context.main_context import MainContext

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
