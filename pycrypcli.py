import getpass
import sys

from client import Client


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
    return client.register(username, mail, password)


def login() -> str:
    username: str = input("Username: ")
    password: str = getpass.getpass("Password: ")
    return client.login(username, password)


def mainloop():
    print("Logged in successfully.")


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
