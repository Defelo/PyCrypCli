import getpass
import sys

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


def mainloop():
    status: dict = client.info()
    username: str = status["name"]
    print(f"Logged in as {username}.")
    while True:
        prompt: str = ">>> "
        command: str = input(prompt)
        if command in ("exit", "quit"):
            die("Logged out.")
        elif command == "help":
            print("status")
            # print("hostname")
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
        elif command == "status":
            online: int = client.info()["online"]
            print(f"Online players: {online}")
        elif command == "clear":
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
