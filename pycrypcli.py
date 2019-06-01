import getpass
import os
import re
import sys
from typing import List, Optional, Tuple

from client import Client
from exceptions import *


def die(*args, **kwargs):
    print(*args, **kwargs)
    exit()


SERVER: str = "wss://ws.cryptic-game.net/"
SESSION_FILE: List[str] = [os.path.expanduser("~"), ".config", "pycrypcli", "session.json"]

client: Client = Client(SERVER)


def load_session() -> Optional[str]:
    try:
        content: dict = json.load(open(os.path.join(*SESSION_FILE)))
        if "token" in content:
            return content["token"]
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        pass
    return None


def save_session(token: str):
    for i in range(1, len(SESSION_FILE)):
        path: str = os.path.join(*SESSION_FILE[:i])
        if not os.path.exists(path):
            os.mkdir(path)
    path: str = os.path.join(*SESSION_FILE)
    with open(path, "w") as file:
        json.dump({"token": token}, file)
        file.flush()


def delete_session():
    os.remove(os.path.join(*SESSION_FILE))


def register() -> str:
    username: str = input("Username: ")
    mail: str = input("Email Address: ")
    password: str = getpass.getpass("Password: ")
    confirm_password: str = getpass.getpass("Confirm Password: ")
    if password != confirm_password:
        die("Passwords don't match.")
    try:
        return client.register(username, mail, password)
    except WeakPasswordException:
        die("Password is too weak.")
    except UsernameAlreadyExistsException:
        die("Username already exists.")
    except InvalidEmailException:
        die("Invalid email")


def login() -> str:
    username: str = input("Username: ")
    password: str = getpass.getpass("Password: ")
    try:
        return client.login(username, password)
    except InvalidLoginException:
        die("Invalid Login Credentials.")


def get_file(device_uuid: str, filename: str) -> Optional[dict]:
    files: List[dict] = client.get_all_files(device_uuid)
    for file in files:
        if file["filename"] == filename:
            return file
    return None


def get_host() -> Tuple[str, str]:
    devices: List[dict] = client.get_all_devices()
    if not devices:
        devices: List[dict] = [client.create_device()]
    hostname: str = devices[0]["name"]
    device_uuid: str = devices[0]["uuid"]
    return hostname, device_uuid


def is_uuid(x: str) -> bool:
    return bool(re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}", x))


def extract_wallet(content: str) -> Optional[List[str]]:
    if re.match(r"^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12} [0-9a-f]{10}$", content):
        return content.split()
    return None


def mainloop():
    history: List[str] = []
    username: str = client.info()["name"]
    print(f"Logged in as {username}.")
    hostname, device_uuid = get_host()
    while True:
        prompt: str = f"\033[32m{username}@{hostname} $ \033[0m"
        cmd: str = None
        args: List[str] = None
        try:
            command: List[str] = input(prompt).lstrip().split()
            if not command:
                continue
            cmd, *args = command
        except EOFError:
            print()
            exit()
        except KeyboardInterrupt:
            print()
            continue
        if cmd in ("exit", "quit"):
            exit()
        elif cmd == "logout":
            delete_session()
            die("Logged out.")
        elif cmd == "help":
            print("status")
            print("whoami")
            print("hostname")
            print("ls")
            print("l")
            print("dir")
            print("touch")
            print("cat")
            print("rm")
            print("cp")
            print("mv")
            print("exit")
            print("quit")
            print("logout")
            print("clear")
            print("history")
            print("morphcoin")
            print("pay")
            # print("service")
            # print("spot")
            # print("connect")
        elif cmd == "status":
            online: int = client.info()["online"]
            print(f"Online players: {online}")
        elif cmd == "whoami":
            username: str = client.info()["name"]
            print(username)
        elif cmd == "hostname":
            if args:
                name: str = " ".join(args)
                client.change_device_name(device_uuid, name)
            hostname, device_uuid = get_host()
            if not args:
                print(hostname)
        elif cmd in ("ls", "l", "dir"):
            files: List[dict] = client.get_all_files(device_uuid)
            for file in files:
                print(file["filename"])
        elif cmd == "touch":
            if not args:
                print("usage: touch <filename> [content]")
                continue
            filename, *content = args
            content: str = " ".join(content)
            client.create_file(device_uuid, filename, content)
        elif cmd == "cat":
            if not args:
                print("usage: cat <filename>")
                continue
            filename: str = args[0]
            file: dict = get_file(device_uuid, filename)
            if file is None:
                print("File does not exist.")
                continue
            print(file["content"])
        elif cmd == "rm":
            if not args:
                print("usage: rm <filename>")
                continue
            filename: str = args[0]
            file: dict = get_file(device_uuid, filename)
            if file is None:
                print("File does not exist.")
                continue
            client.remove_file(device_uuid, file["uuid"])
        elif cmd == "cp":
            if len(args) != 2:
                print("usage: cp <source> <destination>")
                continue
            source: str = args[0]
            destination: str = args[1]
            file: dict = get_file(device_uuid, source)
            if file is None:
                print("File does not exist.")
                continue
            client.create_file(device_uuid, destination, file["content"])
        elif cmd == "mv":
            if len(args) != 2:
                print("usage: mv <source> <destination>")
                continue
            source: str = args[0]
            destination: str = args[1]
            file: dict = get_file(device_uuid, source)
            if file is None:
                print("File does not exist.")
                continue
            client.create_file(device_uuid, destination, file["content"])
            client.remove_file(device_uuid, file["uuid"])
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
                    uuid, key = client.create_wallet()
                    client.create_file(device_uuid, filename, uuid + " " + key)
                except AlreadyOwnAWalletException:
                    print("You already own a wallet")
            elif args[0] == "look":
                file: dict = get_file(device_uuid, filename)
                if file is None:
                    print("File does not exist.")
                    continue
                wallet: Tuple[str, str] = extract_wallet(file["content"])
                if wallet is None:
                    print("File is no wallet file.")
                    continue
                try:
                    amount: int = client.get_wallet(*wallet)["amount"]
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
            file: dict = get_file(device_uuid, args[0])
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
                client.get_wallet(wallet_uuid, wallet_key)
            except InvalidWalletException:
                print("Invalid wallet file. Wallet does not exist.")
                continue
            except InvalidKeyException:
                print("Invalid wallet file. Key is incorrect.")
                continue
            try:
                client.send(wallet_uuid, wallet_key, receiver, amount, " ".join(args[3:]))
                print(f"Sent {amount} morphcoin to {receiver}.")
            except SourceWalletTransactionDebtException:
                print("The source wallet would make debt. Transaction canceled.")
            except InvalidWalletException:
                print("Destination wallet does not exist.")
        else:
            print("Command could not be found.")
            print("Type `help` for a list of commands.")
        history.append(cmd + " ".join(args))


def main():
    if len(sys.argv) > 1:
        arg: str = sys.argv[1]
        if arg.lower() in ("signup", "register"):
            save_session(register())
        else:
            print("Python Cryptic Game Client (https://github.com/Defelo/PyCrypCli)")
            print()
            die(f"Usage: {sys.argv[0]} [help|signup]")
    else:
        token: str = load_session()
        if token is not None:
            try:
                client.session(token)
            except InvalidSessionTokenException:
                delete_session()
                save_session(login())
        else:
            save_session(login())
    mainloop()


if __name__ == '__main__':
    main()
