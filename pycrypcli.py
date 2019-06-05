import getpass
import os
from typing import List, Optional, Tuple, Dict

from commands.command import make_commands, COMMAND_FUNCTION, command
from exceptions import *
from game import Game

try:
    import readline
except ImportError:
    import pyreadline as readline

SERVER: str = "wss://ws.cryptic-game.net/"


def show_help(commands):
    print("Available commands:")
    max_length: int = max(len(cmd[0]) for cmd in commands)
    for com, desc in commands:
        com: str = com.ljust(max_length)
        print(f" - {com}    {desc}")


class Frontend(Game):
    LOGIN_COMMANDS: List[Tuple[str, str]] = [
        ("login", "Login with an existing account"),
        ("register", "Create a new account"),
        ("signup", "Create a new account"),
        ("help", "Show a list of available commands"),
        ("exit", "Exit PyCrypCli"),
        ("quit", "Exit PyCrypCli"),
    ]

    def __init__(self, server: str, session_file: List[str]):
        super().__init__(server)
        self.session_file: List[str] = session_file

        self.login_stack: List[str] = []
        self.history: List[str] = []

        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        readline.set_completer_delims(" ")
        self.override_completions: List[str] = None

    def complete_arguments(self, cmd: str, args: List[str]) -> List[str]:
        if cmd in ("cat", "rm", "cp", "mv", "pay"):
            if len(args) == 1:
                return [file["filename"] for file in self.client.get_all_files(self.device_uuid)]
        elif cmd == "morphcoin":
            if len(args) == 1:
                return ["create", "look"]
            elif len(args) == 2:
                if args[0] == "look":
                    return [file["filename"] for file in self.client.get_all_files(self.device_uuid)]
        elif cmd == "service":
            if len(args) == 1:
                return ["create", "list", "bruteforce", "portscan"]
            elif len(args) == 2:
                if args[0] == "create":
                    return ["bruteforce", "portscan", "ssh", "telnet"]
                elif args[0] == "bruteforce":
                    return ["ssh", "telnet"]
        return []

    def complete_command(self, text: str) -> List[str]:
        if self.override_completions is not None:
            return self.override_completions

        cmd, *args = text.split(" ") or [""]
        if not self.login_stack:
            if not args:
                return [cmd[0] for cmd in self.LOGIN_COMMANDS]
        else:
            if not args:
                return [cmd for cmd in self.COMMANDS]
            else:
                return self.complete_arguments(cmd, args)
        return []

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
            self.override_completions: List[str] = None
            if choice in options:
                return choice
            print(f"'{choice}' is not one of the following:", ", ".join(options))

    def remote_login(self, uuid: str):
        self.login_stack.append(uuid)
        self.update_host(uuid)

    def login_loop(self):
        logged_in: bool = False
        try:
            if self.load_session():
                logged_in: bool = True
                self.mainloop()
        except InvalidSessionTokenException:
            self.delete_session()

        if not logged_in:
            print("You are not logged in.")
            print("Type `register` to create a new account or `login` if you already have one.")

        while True:
            cmd: str = None
            try:
                cmd: str = input("$ ").strip()
                if not cmd:
                    continue
            except EOFError:
                print("exit")
                exit()
            except KeyboardInterrupt:
                print("^C")
                continue

            if cmd in ("exit", "quit"):
                exit()
            elif cmd == "login":
                if self.login():
                    self.mainloop()
                else:
                    print("Login failed.")
            elif cmd in ("register", "signup"):
                if self.register():
                    self.mainloop()
                else:
                    print("Registration failed.")
            elif cmd == "help":
                show_help(self.LOGIN_COMMANDS)
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")

    def load_session(self) -> bool:
        try:
            content: dict = json.load(open(os.path.join(*self.session_file)))
            if "token" in content:
                self.session_token: str = content["token"]
                self.client.session(self.session_token)
                return True
        except FileNotFoundError:
            pass
        except json.JSONDecodeError:
            pass
        return False

    def save_session(self):
        for i in range(1, len(self.session_file)):
            path: str = os.path.join(*self.session_file[:i])
            if not os.path.exists(path):
                os.mkdir(path)
        path: str = os.path.join(*self.session_file)
        with open(path, "w") as file:
            json.dump({"token": self.session_token}, file)
            file.flush()

    def delete_session(self):
        os.remove(os.path.join(*self.session_file))

    def register(self) -> bool:
        username: str = input("Username: ")
        mail: str = input("Email Address: ")
        password: str = getpass.getpass("Password: ")
        confirm_password: str = getpass.getpass("Confirm Password: ")
        if password != confirm_password:
            print("Passwords don't match.")
            return False
        try:
            self.session_token: str = self.client.register(username, mail, password)
            self.save_session()
            self.update_host()
            self.client.create_service(self.device_uuid, "ssh")
            return True
        except WeakPasswordException:
            print("Password is too weak.")
        except UsernameAlreadyExistsException:
            print("Username already exists.")
        except InvalidEmailException:
            print("Invalid email")
        return False

    def login(self) -> bool:
        username: str = input("Username: ")
        password: str = getpass.getpass("Password: ")
        try:
            self.session_token: str = self.client.login(username, password)
            self.save_session()
            return True
        except InvalidLoginException:
            print("Invalid Login Credentials.")
        return False

    def logout(self):
        self.client.logout()
        self.delete_session()
        print("Logged out.")

    def is_remote(self) -> bool:
        return len(self.login_stack) > 1

    @command(["exit", "quit"], "Exit PyCrypCli (session will be saved)")
    def handle_main_exit(self, *_):
        self.login_stack.pop()
        if self.login_stack:
            self.update_host(self.login_stack[-1])
        else:
            self.client.close()
            exit()

    @command(["logout"], "Delete the current session and exit PyCrypCli")
    def handle_main_logout(self, *_):
        self.login_stack.pop()
        if self.login_stack:
            self.update_host(self.login_stack[-1])
        else:
            self.logout()

    @command(["help"], "Show a list of available commands")
    def handle_main_help(self, *_):
        show_help([(c, d) for c, (d, _) in self.COMMANDS.items()])

    @command(["clear"], "Clear the console")
    def handle_main_clear(self, *_):
        print(end="\033c")

    @command(["history"], "Show the history of commands entered in this session")
    def handle_main_history(self, *_):
        for line in self.history:
            print(line)

    def add_to_history(self, cmd: str):
        if self.history[-1:] != [cmd]:
            self.history.append(cmd)

    def mainloop(self):
        self.history.clear()
        self.update_host()
        self.update_username()
        self.login_stack.append(self.device_uuid)
        print(f"Logged in as {self.username}.")
        while self.login_stack:
            if self.is_remote():
                prompt: str = "\033[38;2;255;64;23m"
            else:
                prompt: str = "\033[38;2;100;221;23m"
            prompt += f"{self.username}@{self.hostname} $ \033[0m"
            try:
                cmd, *args = input(prompt).strip().split(" ")
                if not cmd:
                    continue
            except EOFError:
                print("exit")
                self.handle_main_exit()
                continue
            except KeyboardInterrupt:
                print("^C")
                continue

            self.add_to_history(cmd + " " + " ".join(args))

            if cmd in self.COMMANDS:
                func: COMMAND_FUNCTION = self.COMMANDS[cmd][1]
                func(self, args)
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")

    COMMANDS: Dict[str, Tuple[str, COMMAND_FUNCTION]] = make_commands()


def main():
    print("""\033[32m\033[1m
       ______                 __  _     
      / ____/______  ______  / /_(_)____
     / /   / ___/ / / / __ \/ __/ / ___/
    / /___/ /  / /_/ / /_/ / /_/ / /__  
    \____/_/   \__, / .___/\__/_/\___/  
              /____/_/                  
\033[0m""")
    print("Python Cryptic Game Client (https://github.com/Defelo/PyCrypCli)")
    print("You can always type `help` for a list of available commands.")

    frontend: Frontend = Frontend(SERVER, [os.path.expanduser("~"), ".config", "pycrypcli", "session.json"])
    frontend.login_loop()


if __name__ == '__main__':
    main()
