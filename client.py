from typing import List
from uuid import uuid4

from websocket import WebSocket, create_connection

from exceptions import *


def uuid() -> str:
    return str(uuid4())


class Client:
    def __init__(self, server: str):
        self.websocket: WebSocket = create_connection(server)

    def request(self, command: dict) -> dict:
        self.websocket.send(json.dumps(command))
        return json.loads(self.websocket.recv())

    def microservice(self, ms: str, endpoint: List[str], data: dict) -> dict:
        response: dict = self.request({
            "ms": ms,
            "endpoint": endpoint,
            "data": data,
            "tag": uuid()
        })
        if "error" in response or "data" not in response:
            raise InvalidServerResponseException(response)
        return response["data"]

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

    def info(self) -> dict:
        response: dict = self.request({
            "action": "info"
        })
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def get_all_devices(self) -> List[dict]:
        response: dict = self.microservice("device", ["device", "all"], {})
        if "devices" not in response:
            raise InvalidServerResponseException(response)
        devices: List[dict] = response["devices"]
        return devices

    def change_device_name(self, device_uuid: str, name: str):
        self.microservice("device", ["device", "change_name"], {
            "device_uuid": device_uuid,
            "name": name
        })

    def get_all_files(self, device_uuid: str) -> List[dict]:
        response: dict = self.microservice("device", ["file", "all"], {
            "device_uuid": device_uuid
        })
        if "files" not in response:
            raise InvalidServerResponseException(response)
        files: List[dict] = response["files"]
        return files
