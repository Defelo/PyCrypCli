from websocket import WebSocket, create_connection

from exceptions import *


class Client:
    def __init__(self, server: str):
        self.websocket: WebSocket = create_connection(server)

    def request(self, command: dict) -> dict:
        self.websocket.send(json.dumps(command))
        return json.loads(self.websocket.recv())

    def register(self, username: str, email: str, password: str) -> str:
        response: dict = self.request({
            "action": "register",
            "name": username,
            "mail": email,
            "password": password
        })
        if "error" in response:
            error: str = response["error"]
            if error.startswith("password invalid (condition:"):
                raise WeakPasswordException()
            if error == "username already exists":
                raise UsernameAlreadyExistsException()
            if error == "email invalid":
                raise InvalidEmailException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            raise InvalidServerResponseException(response)
        return response["token"]

    def login(self, username: str, password: str) -> str:
        response: dict = self.request({
            "action": "login",
            "name": username,
            "password": password
        })
        if "error" in response:
            error = response["error"]
            if error == "permission denied":
                raise InvalidLoginException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            raise InvalidServerResponseException(response)
        return response["token"]
