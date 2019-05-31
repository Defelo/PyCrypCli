import getpass

from client import Client

SERVER: str = "wss://ws.cryptic-game.net/"

client: Client = Client(SERVER)

username: str = input("Username: ")
password: str = getpass.getpass("Password: ")

response: dict = client.request({"action": "login", "name": username, "password": password})
if "error" in response:
    print("Error:", response["error"])
    exit()

token: str = response["token"]
print(f"Logged in as {username}. Token: {token}")
