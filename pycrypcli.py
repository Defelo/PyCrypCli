import getpass

from client import Client
from exceptions import InvalidLoginException

SERVER: str = "wss://ws.cryptic-game.net/"

client: Client = Client(SERVER)

username: str = input("Username: ")
password: str = getpass.getpass("Password: ")

token = None
try:
    token: str = client.login(username, password)
except InvalidLoginException:
    print("Invalid Login Credentials")
    exit()

print(f"Logged in as {username}. Token: {token}")
