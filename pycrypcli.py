import getpass
import os
import re
from typing import List, Optional, Tuple

from client import Client
from exceptions import *

try:
    import readline
except ImportError:
    import pyreadline as readline

SERVER: str = "wss://ws.cryptic-game.net/"


def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", x))


def extract_wallet(content: str) -> Optional[List[str]]:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        return content.split()
    return None


class Game:
    LOGIN_COMMANDS: List[Tuple[str, str]] = [
        ("login", "Login with an existing account"),
        ("register", "Create a new account"),
        ("signup", "Create a new account"),
        ("help", "Show a list of available commands"),
        ("exit", "Exit PyCrypCli"),
        ("quit", "Exit PyCrypCli"),
    ]

    COMMANDS: List[Tuple[str, str]] = [
        ("status", "Indicate how many players are online"),
        ("whoami", "Print the name of the current user"),
        ("hostname", "Show or modify the name of the device"),
        ("help", "Show a list of available commands"),
        ("ls", "List all files"),
        ("l", "List all files"),
        ("dir", "List all files"),
        ("touch", "Create a new file with given content"),
        ("cat", "Print the content of a file"),
        ("rm", "Remove a file"),
        ("cp", "Create a copy of a file"),
        ("mv", "Rename a file"),
        ("exit", "Exit PyCrypCli (session will be saved)"),
        ("quit", "Exit PyCrypCli (session will be saved)"),
        ("logout", "Delete the current session and exit PyCrypCli"),
        ("clear", "Clear the console"),
        ("history", "Show the history of commands entered in this session"),
        ("morphcoin", "Manage your Morphcoin wallet"),
        ("pay", "Send Morphcoins to another wallet"),
        ("service", "Create or use a service"),
        ("spot", "Find a random device in the network"),
        ("connect", "Connect to a device you hacked before")
    ]

    def __init__(self, server: str, session_file: List[str]):
        self.client: Client = Client(server)
        self.session_file: List[str] = session_file
        self.session_token: str = None

        self.device_uuid: str = None
        self.hostname: str = None
        self.username: str = None

        self.login_stack: List[str] = []

        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
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
                return [cmd[0] for cmd in self.COMMANDS]
            else:
                return self.complete_arguments(cmd, args)
        return []

    def completer(self, text: str, state: int) -> Optional[str]:
        options: List[str] = self.complete_command(readline.get_line_buffer())
        options: List[str] = [o + " " for o in sorted(options) if o.startswith(text)]

        if state < len(options):
            return options[state]
        return None

    def logout(self):
        self.client.close()
        self.delete_session()
        print("Logged out.")

    def login_loop(self):
        logged_in: bool = False
        try:
            if self.load_session():
                logged_in: bool = True
                self.mainloop()
        except InvalidSessionTokenException:
            self.delete_session()
            self.client.close()

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
                print("Available commands:")
                max_length: int = max(len(command[0]) for command in self.LOGIN_COMMANDS)
                for com, desc in self.LOGIN_COMMANDS:
                    com: str = com.ljust(max_length)
                    print(f" - {com}    {desc}")
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")

    def load_session(self) -> bool:
        try:
            content: dict = json.load(open(os.path.join(*self.session_file)))
            if "token" in content:
                self.session_token: str = content["token"]
                self.client.init()
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
        self.client.init()
        try:
            self.session_token: str = self.client.register(username, mail, password)
            self.save_session()
            return True
        except WeakPasswordException:
            print("Password is too weak.")
        except UsernameAlreadyExistsException:
            print("Username already exists.")
        except InvalidEmailException:
            print("Invalid email")
        self.client.close()
        return False

    def login(self) -> bool:
        username: str = input("Username: ")
        password: str = getpass.getpass("Password: ")
        self.client.init()
        try:
            self.session_token: str = self.client.login(username, password)
            self.save_session()
            return True
        except InvalidLoginException:
            print("Invalid Login Credentials.")
        self.client.close()
        return False

    def get_file(self, filename: str) -> Optional[dict]:
        files: List[dict] = self.client.get_all_files(self.device_uuid)
        for file in files:
            if file["filename"] == filename:
                return file
        return None

    def get_service(self, name: str) -> Optional[dict]:
        services: List[dict] = self.client.get_services(self.device_uuid)
        for service in services:
            if service["name"] == name:
                return service
        return None

    def update_host(self, device_uuid: str = None):
        if device_uuid is None:
            devices: List[dict] = self.client.get_all_devices()
            if not devices:
                devices: List[dict] = [self.client.create_device()]
            self.hostname: str = devices[0]["name"]
            self.device_uuid: str = devices[0]["uuid"]
        else:
            self.device_uuid: str = device_uuid
            self.hostname: str = self.client.device_info(device_uuid)["name"]

    def update_username(self):
        self.username: str = self.client.info()["name"]

    def remote(self) -> bool:
        return len(self.login_stack) > 1

    def mainloop(self):
        history: List[str] = []
        self.update_host()
        self.update_username()
        self.login_stack.append(self.device_uuid)
        print(f"Logged in as {self.username}.")
        while True:
            if self.remote():
                prompt: str = "\033[38;2;255;64;23m"
            else:
                prompt: str = "\033[38;2;100;221;23m"
            prompt += f"{self.username}@{self.hostname} $ \033[0m"
            cmd: str = None
            args: List[str] = None
            try:
                command: List[str] = input(prompt).lstrip().split()
                if not command:
                    continue
                cmd, *args = command
            except EOFError:
                print("exit")
                self.login_stack.pop()
                if self.login_stack:
                    self.update_host(self.login_stack[-1])
                    continue
                else:
                    exit()
            except KeyboardInterrupt:
                print("^C")
                continue

            command: str = cmd + " " + " ".join(args)
            if history[-1:] != [command]:
                history.append(command)

            if cmd in ("exit", "quit"):
                self.login_stack.pop()
                if self.login_stack:
                    self.update_host(self.login_stack[-1])
                else:
                    exit()
            elif cmd == "logout":
                self.login_stack.pop()
                if self.login_stack:
                    self.update_host(self.login_stack[-1])
                else:
                    self.logout()
                    break
            elif cmd == "help":
                print("Available commands:")
                max_length: int = max(len(command[0]) for command in self.COMMANDS)
                for com, desc in self.COMMANDS:
                    com: str = com.ljust(max_length)
                    print(f" - {com}    {desc}")
            elif cmd == "status":
                online: int = self.client.info()["online"]
                print(f"Online players: {online}")
            elif cmd == "whoami":
                self.update_username()
                print(self.username)
            elif cmd == "hostname":
                if args:
                    name: str = " ".join(args)
                    self.client.change_device_name(self.device_uuid, name)
                self.update_host(self.device_uuid)
                if not args:
                    print(self.hostname)
            elif cmd in ("ls", "l", "dir"):
                files: List[dict] = self.client.get_all_files(self.device_uuid)
                for file in files:
                    print(file["filename"])
            elif cmd == "touch":
                if not args:
                    print("usage: touch <filename> [content]")
                    continue
                filename, *content = args
                content: str = " ".join(content)
                self.client.create_file(self.device_uuid, filename, content)
            elif cmd == "cat":
                if not args:
                    print("usage: cat <filename>")
                    continue
                filename: str = args[0]
                file: dict = self.get_file(filename)
                if file is None:
                    print("File does not exist.")
                    continue
                print(file["content"])
            elif cmd == "rm":
                if not args:
                    print("usage: rm <filename>")
                    continue
                filename: str = args[0]
                file: dict = self.get_file(filename)
                if file is None:
                    print("File does not exist.")
                    continue
                content: str = file["content"]
                wallet: Tuple[str, str] = extract_wallet(content)
                if wallet is not None:
                    wallet_uuid, wallet_key = wallet
                    try:
                        amount: int = self.client.get_wallet(wallet_uuid, wallet_key)["amount"]
                        while True:
                            self.override_completions: List[str] = ["yes", "no"]
                            choice: str = input(f"\033[38;2;255;51;51mThis file contains {amount} morphcoin. "
                                                f"Do you want to delete the corresponding wallet? [yes|no] \033[0m")
                            self.override_completions: List[str] = None
                            choice: str = choice.strip()
                            if choice in ("yes", "no"):
                                break
                            print(f"'{choice}' is not one of the following: yes, no")
                        if choice == "yes":
                            self.client.delete_wallet(wallet_uuid, wallet_key)
                            print("The wallet has been deleted.")
                        else:
                            print("The following key might now be the only way to access your wallet.")
                            print("Note that you can't create another wallet without this key.")
                            print(content)
                    except InvalidKeyException:
                        pass
                self.client.remove_file(self.device_uuid, file["uuid"])
            elif cmd == "cp":
                if len(args) != 2:
                    print("usage: cp <source> <destination>")
                    continue
                source: str = args[0]
                destination: str = args[1]
                file: dict = self.get_file(source)
                if file is None:
                    print("File does not exist.")
                    continue
                self.client.create_file(self.device_uuid, destination, file["content"])
            elif cmd == "mv":
                if len(args) != 2:
                    print("usage: mv <source> <destination>")
                    continue
                source: str = args[0]
                destination: str = args[1]
                file: dict = self.get_file(source)
                if file is None:
                    print("File does not exist.")
                    continue
                self.client.create_file(self.device_uuid, destination, file["content"])
                self.client.remove_file(self.device_uuid, file["uuid"])
            elif cmd == "clear":
                print(end="\033c")
            elif cmd == "history":
                for line in history:
                    print(line)
            elif cmd == "morphcoin":
                if len(args) != 2 or args[0] not in ("look", "create"):
                    print("usage: morphcoin look|create <filename>")
                    continue
                filename: str = args[1]
                if args[0] == "create":
                    try:
                        uuid, key = self.client.create_wallet()
                        self.client.create_file(self.device_uuid, filename, uuid + " " + key)
                    except AlreadyOwnAWalletException:
                        print("You already own a wallet")
                elif args[0] == "look":
                    file: dict = self.get_file(filename)
                    if file is None:
                        print("File does not exist.")
                        continue
                    wallet: Tuple[str, str] = extract_wallet(file["content"])
                    if wallet is None:
                        print("File is no wallet file.")
                        continue
                    try:
                        amount: int = self.client.get_wallet(*wallet)["amount"]
                    except InvalidWalletException:
                        print("Invalid wallet file. Wallet does not exist.")
                        continue
                    except InvalidKeyException:
                        print("Invalid wallet file. Key is incorrect.")
                        continue
                    print(f"{amount} morphcoin")
            elif cmd == "pay":
                if len(args) < 3:
                    print("usage: pay <filename> <receiver> <amount> [usage]")
                    continue
                file: dict = self.get_file(args[0])
                if file is None:
                    print("File does not exist.")
                    continue
                wallet: Tuple[str, str] = extract_wallet(file["content"])
                if wallet is None:
                    print("File is no wallet file.")
                    continue
                wallet_uuid, wallet_key = wallet
                receiver: str = args[1]
                if not is_uuid(receiver):
                    print("Invalid receiver.")
                    continue
                if not args[2].isnumeric():
                    print("amount is not a number.")
                    continue
                amount: int = int(args[2])
                try:
                    self.client.get_wallet(wallet_uuid, wallet_key)
                except InvalidWalletException:
                    print("Invalid wallet file. Wallet does not exist.")
                    continue
                except InvalidKeyException:
                    print("Invalid wallet file. Key is incorrect.")
                    continue
                try:
                    self.client.send(wallet_uuid, wallet_key, receiver, amount, " ".join(args[3:]))
                    print(f"Sent {amount} morphcoin to {receiver}.")
                except SourceWalletTransactionDebtException:
                    print("The source wallet would make debt. Transaction canceled.")
                except InvalidWalletException:
                    print("Destination wallet does not exist.")
            elif cmd == "service":
                if len(args) < 1 or args[0] not in ("create", "list", "bruteforce", "portscan"):
                    print("usage: service create|list|bruteforce|portscan")
                elif args[0] == "create":
                    if len(args) != 2 or args[1] not in ("bruteforce", "portscan", "telnet", "ssh"):
                        print("usage: service create <bruteforce|portscan|telnet|ssh>")
                        continue
                    try:
                        self.client.create_service(self.device_uuid, args[1])
                        print("Service was created")
                    except AlreadyOwnServiceException:
                        print("You already created this service")
                elif args[0] == "list":
                    services: List[dict] = self.client.get_services(self.device_uuid)
                    print("Services:")
                    for service in services:
                        name: str = service["name"]
                        port: int = service["running_port"]
                        line: str = f" - {name}"
                        if port is not None:
                            line += f" on port {port}"
                        print(line)
                elif args[0] == "bruteforce":
                    if len(args) != 3:
                        print("usage: service bruteforce <target-device> <target-service>")
                        continue
                    target_device: str = args[1]
                    target_service: str = args[2]
                    if not is_uuid(target_device):
                        print("Invalid target device")
                        continue
                    if not is_uuid(target_service):
                        print("Invalid target service")
                        continue
                    service: dict = self.get_service("bruteforce")
                    if service is None:
                        print("You have to create a bruteforce service before you use it")
                        continue
                    try:
                        result: dict = self.client.use_service(
                            self.device_uuid, service["uuid"],
                            target_device=target_device, target_service=target_service
                        )
                        assert result["ok"]
                        if "access" in result:
                            if result["access"]:
                                print("Access granted - use `connect <device>`")
                            else:
                                print("Access denied. The bruteforce attack was not successful")
                        else:
                            print("You started a bruteforce attack")
                    except UnknownServiceException:
                        print("Unknown service. Attack couldn't be started.")
                elif args[0] == "portscan":
                    if len(args) != 2:
                        print("usage: service portscan <device>")
                        continue
                    target: str = args[1]
                    if not is_uuid(target):
                        print("Invalid target")
                        continue
                    service: dict = self.get_service("portscan")
                    if service is None:
                        print("You have to create a portscan service before you use it")
                        continue
                    result: dict = self.client.use_service(self.device_uuid, service["uuid"], target_device=target)
                    if not result["services"]:
                        print("That device doesn't have any running services")
                    for service in result["services"]:
                        name: str = service["name"]
                        uuid: str = service["uuid"]
                        port: int = service["running_port"]
                        print(f" - {name} on port {port} (UUID: {uuid})")
            elif cmd == "spot":
                device: dict = self.client.spot()
                name: str = device["name"]
                powered: bool = device["powered_on"]
                uuid: str = device["uuid"]
                powered_text: str = ["\033[38;2;255;51;51mno", "\033[38;2;100;246;23myes"][powered] + "\033[0m"
                print(f"Name: '{name}'")
                print(f"UUID: {uuid}")
                print(f"Powered on: {powered_text}")
                service: dict = self.get_service("portscan")
                if service is not None:
                    print("Services:")
                    result: dict = self.client.use_service(self.device_uuid, service["uuid"], target_device=uuid)
                    if not result["services"]:
                        print("  This device doesn't have any running services")
                    for service in result["services"]:
                        name: str = service["name"]
                        uuid: str = service["uuid"]
                        port: int = service["running_port"]
                        print(f" - {name} on port {port} (UUID: {uuid})")
            elif cmd == "connect":
                if len(args) != 1:
                    print("usage: connect <device>")
                    continue
                uuid: str = args[0]
                if not is_uuid(uuid):
                    print("Invalid device")
                    continue
                if self.client.part_owner(uuid):
                    self.login_stack.append(uuid)
                    self.update_host(uuid)
                else:
                    print("Access denied")
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")


def main():
    print("Python Cryptic Game Client (https://github.com/Defelo/PyCrypCli)")
    print("You can always type `help` for a list of available commands.")

    game: Game = Game(SERVER, [os.path.expanduser("~"), ".config", "pycrypcli", "session.json"])
    game.login_loop()


if __name__ == '__main__':
    main()
