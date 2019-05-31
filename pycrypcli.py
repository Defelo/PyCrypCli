import getpass
import sys
from typing import List

from client import Client
from exceptions import *


def die(*args, **kwargs):
    print(*args, **kwargs)
    exit()


SERVER: str = "wss://ws.cryptic-game.net/"

client: Client = Client(SERVER)


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


def logout():
    die("Logged out.")


def mainloop():
    status: dict = client.info()
    username: str = status["name"]
    print(f"Logged in as {username}.")
    devices: List[dict] = client.get_all_devices()
    assert devices, "no device"
    hostname: str = devices[0]["name"]
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
            logout()
        except KeyboardInterrupt:
            print()
            continue
        if cmd in ("exit", "quit"):
            logout()
        elif cmd == "help":
            print("status")
            print("whoami")
            print("hostname")
            # print("ls")
            # print("l")
            # print("dir")
            # print("touch")
            # print("cat")
            # print("rm")
            # print("cp")
            # print("mv")
            print("exit")
            print("quit")
            print("clear")
            # print("history")
            # print("morphcoin")
            # print("pay")
            # print("service")
            # print("spot")
            # print("connect")
        elif cmd == "status":
            online: int = client.info()["online"]
            print(f"Online players: {online}")
        elif cmd == "whoami":
            status: dict = client.info()
            username: str = status["name"]
            print(username)
        elif cmd == "hostname":
            devices: List[dict] = client.get_all_devices()
            assert devices, "no device"
            if args:
                name: str = " ".join(args)
                client.change_device_name(devices[0]["uuid"], name)
            devices: List[dict] = client.get_all_devices()
            hostname: str = devices[0]["name"]
            if not args:
                print(hostname)
        elif cmd == "clear":
            print(end="\033c")
        else:
            print("Command could not be found.")
            print("Type `help` for a list of commands.")


def main():
    if len(sys.argv) > 1:
        arg: str = sys.argv[1]
        if arg.lower() in ("signup", "register"):
            register()
        else:
            print("Python Cryptic Game Client (https://cryptic-game.net/)")
            print()
            die(f"Usage: {sys.argv[0]} [help|signup]")
    else:
        login()
    mainloop()


if __name__ == '__main__':
    main()
