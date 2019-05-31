import getpass
import json

import websocket

SERVER = "wss://ws.cryptic-game.net/"
ws = websocket.create_connection(SERVER)


def request(command):
    ws.send(json.dumps(command))
    return json.loads(ws.recv())


username = input("Username: ")
password = getpass.getpass("Password: ")

response = request({"action": "login", "name": username, "password": password})
if "error" in response:
    print("Error:", response["error"])
    exit()

token = response["token"]
print(f"Logged in as {username}. Token: {token}")
