import getpass
import os
import sys
from typing import List, Optional, Tuple, Dict

from PyCrypCli.commands.command import make_commands, COMMAND_FUNCTION, command, CTX_LOGIN, CTX_MAIN, CTX_DEVICE
from PyCrypCli.exceptions import *
from PyCrypCli.game import Game

try:
    import readline
except ImportError:
    import pyreadline as readline

SERVER: str = "wss://ws.cryptic-game.net/"
if len(sys.argv) > 1:
    SERVER: str = sys.argv[1]
    if SERVER.lower() == "test":
        SERVER: str = "wss://ws.test.cryptic-game.net/"
    elif not SERVER.startswith("wss://") and not SERVER.startswith("ws://"):
        SERVER: str = "ws://" + SERVER


def show_help(commands):
    print("Available commands:")
    max_length: int = max(len(cmd[0]) for cmd in commands)
    for com, desc in commands:
        com: str = com.ljust(max_length)
        print(f" - {com}    {desc}")


class Frontend(Game):
    def __init__(self, server: str, config_file: List[str]):
        super().__init__(server)
        self.config_file: List[str] = config_file

        self.history: List[str] = []

        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        readline.set_completer_delims(" ")
        self.override_completions: Optional[List[str]] = None

        try:
            self.load_session()
        except InvalidSessionTokenException:
            self.delete_session()

    def complete_arguments(self, cmd: str, args: List[str]) -> List[str]:
        if cmd in ("cat", "touch", "rm", "cp", "mv", "pay"):
            if len(args) == 1:
                return self.get_filenames()
        elif cmd == "morphcoin":
            if len(args) == 1:
                return ["create", "list", "look", "transactions", "reset"]
            elif len(args) == 2:
                if args[0] in ("look", "transactions"):
                    return self.get_filenames()
        elif cmd == "service":
            if len(args) == 1:
                return ["create", "list", "delete", "bruteforce", "portscan"]
            elif len(args) == 2:
                if args[0] in ("create", "delete"):
                    return ["bruteforce", "portscan", "ssh", "telnet", "miner"]
                elif args[0] == "bruteforce":
                    return ["ssh", "telnet"]
            elif len(args) == 3:
                if args[0] == "create" and args[1] == "miner":
                    return self.get_filenames()
        elif cmd == "miner":
            if len(args) == 1:
                return ["look", "power", "wallet"]
        elif cmd == "device":
            if len(args) == 1:
                return ["list", "create", "connect"]
            elif len(args) == 2:
                if args[0] == "connect":
                    device_names: List[str] = [device.name for device in self.client.get_devices()]
                    return [name for name in device_names if device_names.count(name) == 1]
        elif cmd == "remote":
            if len(args) == 1:
                return ["list", "connect"]
            elif len(args) == 2:
                if args[0] == "connect":
                    device_names: List[str] = [device.name for device in self.get_hacked_devices()]
                    return [name for name in device_names if device_names.count(name) == 1]
        elif cmd == "inventory":
            if len(args) == 1:
                return ["list", "trade"]
            elif len(args) == 2:
                if args[0] == "trade":
                    return [element.element_name.replace(" ", "") for element in self.client.inventory_list()]
        elif cmd == "shop":
            if len(args) == 1:
                return ["list", "buy"]
            elif len(args) == 2:
                if args[0] == "buy":
                    return [name.replace(" ", "") for name in self.client.shop_list()]
            elif len(args) == 3:
                if args[0] == "buy":
                    return self.get_filenames()
        return []

    def complete_command(self, text: str) -> List[str]:
        if self.override_completions is not None:
            return self.override_completions

        cmd, *args = text.split(" ") or [""]
        if not args:
            return [cmd for cmd in self.COMMANDS[self.get_context()]]
        else:
            return self.complete_arguments(cmd, args)

    def completer(self, text: str, state: int) -> Optional[str]:
        options: List[str] = self.complete_command(readline.get_line_buffer())
        options: List[str] = [o + " " for o in sorted(options) if o.startswith(text)]

        if state < len(options):
            return options[state]
        return None

    def ask(self, prompt: str, options: List[str]) -> str:
        while True:
            self.override_completions: List[str] = options
            choice: str = input(prompt).strip()
            self.override_completions: Optional[List[str]] = None
            if choice in options:
                return choice
            print(f"'{choice}' is not one of the following:", ", ".join(options))

    def remote_login(self, uuid: str):
        self.login_stack.append(self.client.device_info(uuid))
        self.update_host()

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

    def load_session(self):
        config: dict = self.read_config_file()

        if "token" in config.setdefault("servers", {}).setdefault(self.host, {}):
            self.session_token: str = config["servers"][self.host]["token"]
            self.client.session(self.session_token)

    def save_session(self):
        config: dict = self.read_config_file()
        config.setdefault("servers", {}).setdefault(self.host, {})["token"] = self.session_token
        self.write_config_file(config)

    def delete_session(self):
        config: dict = self.read_config_file()
        if "token" in config.setdefault("servers", {}).setdefault(self.host, {}):
            del config["servers"][self.host]["token"]
        self.write_config_file(config)
        self.session_token = None

    def get_context(self) -> int:
        if not self.is_logged_in():
            return CTX_LOGIN
        if not self.login_stack:
            return CTX_MAIN
        return CTX_DEVICE

    @command(["register", "signup"], CTX_LOGIN, "Create a new account")
    def register(self, *_):
        username: str = input("Username: ")
        mail: str = input("Email Address: ")
        password: str = getpass.getpass("Password: ")
        confirm_password: str = getpass.getpass("Confirm Password: ")
        if password != confirm_password:
            print("Passwords don't match.")
            return
        try:
            self.session_token: str = self.client.register(username, mail, password)
        except WeakPasswordException:
            print("Password is too weak.")
            return
        except UsernameAlreadyExistsException:
            print("Username already exists.")
            return
        except InvalidEmailException:
            print("Invalid email")
            return

        self.save_session()
        self.update_username()
        print(f"Logged in as {self.username}.")

    @command(["login"], CTX_LOGIN, "Login with an existing account")
    def login(self, *_):
        username: str = input("Username: ")
        password: str = getpass.getpass("Password: ")
        try:
            self.session_token: str = self.client.login(username, password)
        except InvalidLoginException:
            print("Invalid Login Credentials.")
            return

        self.save_session()
        self.update_username()
        print(f"Logged in as {self.username}.")

    @command(["exit", "quit"], CTX_LOGIN, "Exit PyCrypCli")
    def handle_main_exit(self, *_):
        exit()

    @command(["exit", "quit"], CTX_MAIN, "Exit PyCrypCli (session will be saved)")
    def handle_main_exit(self, *_):
        self.client.close()
        exit()

    @command(["exit", "quit", "logout"], CTX_DEVICE, "Disconnect from this device")
    def handle_main_exit(self, *_):
        self.login_stack.pop()

    @command(["logout"], CTX_MAIN, "Delete the current session and exit PyCrypCli")
    def handle_main_logout(self, *_):
        self.client.logout()
        self.delete_session()
        print("Logged out.")

    @command(["help"], -1, "Show a list of available commands")
    def handle_main_help(self, *_):
        show_help([(c, d) for c, (d, _) in self.COMMANDS[self.get_context()].items()])

    @command(["clear"], -1, "Clear the console")
    def handle_main_clear(self, *_):
        print(end="\033c")

    @command(["history"], ~CTX_LOGIN, "Show the history of commands entered in this session")
    def handle_main_history(self, *_):
        for line in self.history:
            print(line)

    def add_to_history(self, cmd: str):
        if self.history[-1:] != [cmd]:
            self.history.append(cmd)

    def mainloop(self):
        if not self.is_logged_in():
            print("You are not logged in.")
            print("Type `register` to create a new account or `login` if you already have one.")
        else:
            self.update_username()
            print(f"Logged in as {self.username}.")

        while True:
            context: int = self.get_context()
            self.update_host()

            if context == CTX_LOGIN:
                self.login_loop_presence()
                prompt: str = f"$ "
            else:
                self.main_loop_presence()
                self.update_username()
                if context == CTX_MAIN:
                    prompt: str = f"\033[38;2;53;160;171m[{self.username}]$\033[0m "
                elif self.is_local_device():
                    prompt: str = f"\033[38;2;100;221;23m[{self.username}@{self.get_device().name}]$\033[0m "
                else:
                    prompt: str = f"\033[38;2;255;64;23m[{self.username}@{self.get_device().name}]$\033[0m "

            try:
                cmd, *args = input(prompt).strip().split(" ")
                if not cmd:
                    continue
            except EOFError:  # Ctrl-D
                print("exit")
                cmd, args = "exit", []
            except KeyboardInterrupt:  # Ctrl-C
                print("^C")
                continue

            self.add_to_history(cmd + " " + " ".join(args))

            if cmd in self.COMMANDS[context]:
                func: COMMAND_FUNCTION = self.COMMANDS[context][cmd][1]
                func(self, context, args)
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")

    COMMANDS: Dict[int, Dict[str, Tuple[str, COMMAND_FUNCTION]]] = make_commands()


def main():
    print(
        "\033[32m\033[1m"
        + r"""
       ______                 __  _     
      / ____/______  ______  / /_(_)____
     / /   / ___/ / / / __ \/ __/ / ___/
    / /___/ /  / /_/ / /_/ / /_/ / /__  
    \____/_/   \__, / .___/\__/_/\___/  
              /____/_/                  
"""
        + "\033[0m"
    )
    print("Python Cryptic Game Client (https://github.com/Defelo/PyCrypCli)")
    print("You can always type `help` for a list of available commands.")

    frontend: Frontend = Frontend(SERVER, [os.path.expanduser("~"), ".config", "PyCrypCli", "config.json"])
    frontend.mainloop()


if __name__ == "__main__":
    main()
