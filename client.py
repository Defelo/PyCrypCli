import time
from typing import List, Tuple
from uuid import uuid4

from websocket import WebSocket, create_connection

from exceptions import *
from timer import Timer


def uuid() -> str:
    return str(uuid4())


class Client:
    def __init__(self, server: str):
        self.server: str = server
        self.websocket: WebSocket = None
        self.timer: Timer = None
        self.waiting_for_response: bool = False

    def init(self):
        self.websocket: WebSocket = create_connection(self.server)
        self.timer: Timer = Timer(10, self.info)

    def close(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer: Timer = None

        self.websocket.close()
        self.websocket: WebSocket = None

    def request(self, command: dict) -> dict:
        while self.waiting_for_response:
            time.sleep(0.01)
        self.waiting_for_response: bool = True
        self.websocket.send(json.dumps(command))
        response: dict = json.loads(self.websocket.recv())
        self.waiting_for_response: bool = False
        return response

    def microservice(self, ms: str, endpoint: List[str], data: dict) -> dict:
        response: dict = self.request({
            "ms": ms,
            "endpoint": endpoint,
            "data": data,
            "tag": uuid()
        })
        if "error" in response or "data" not in response:
            raise InvalidServerResponseException(response)
        data: dict = response["data"]
        if "error" in data and data["error"] == "no response - timeout":
            raise NoResponseTimeoutException()
        return data

    def register(self, username: str, email: str, password: str) -> str:
        self.init()
        response: dict = self.request({
            "action": "register",
            "name": username,
            "mail": email,
            "password": password
        })
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error.startswith("password invalid (condition:"):
                raise WeakPasswordException()
            if error == "username already exists":
                raise UsernameAlreadyExistsException()
            if error == "email invalid":
                raise InvalidEmailException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.timer.start()
        return response["token"]

    def login(self, username: str, password: str) -> str:
        self.init()
        response: dict = self.request({
            "action": "login",
            "name": username,
            "password": password
        })
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "permission denied":
                raise InvalidLoginException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.timer.start()
        return response["token"]

    def session(self, token: str):
        self.init()
        response: dict = self.request({
            "action": "session",
            "token": token
        })
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "invalid token":
                raise InvalidSessionTokenException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.timer.start()

    def logout(self):
        self.close()

    def info(self) -> dict:
        response: dict = self.request({
            "action": "info"
        })
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def get_all_devices(self) -> List[dict]:
        response: dict = self.microservice("device", ["device", "all"], {})
        if "error" in response or "devices" not in response:
            raise InvalidServerResponseException(response)
        devices: List[dict] = response["devices"]
        return devices

    def create_device(self) -> dict:
        response: dict = self.microservice("device", ["device", "create"], {})
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def change_device_name(self, device_uuid: str, name: str):
        response: dict = self.microservice("device", ["device", "change_name"], {
            "device_uuid": device_uuid,
            "name": name
        })
        if "error" in response:
            raise InvalidServerResponseException(response)

    def get_all_files(self, device_uuid: str) -> List[dict]:
        response: dict = self.microservice("device", ["file", "all"], {
            "device_uuid": device_uuid
        })
        if "error" in response or "files" not in response:
            raise InvalidServerResponseException(response)
        files: List[dict] = response["files"]
        return files

    def create_file(self, device_uuid: str, filename: str, content: str):
        response: dict = self.microservice("device", ["file", "create"], {
            "device_uuid": device_uuid,
            "filename": filename,
            "content": content
        })
        if "error" in response:
            raise InvalidServerResponseException(response)

    def remove_file(self, device_uuid: str, file_uuid: str):
        response: dict = self.microservice("device", ["file", "delete"], {
            "device_uuid": device_uuid,
            "file_uuid": file_uuid
        })
        if "error" in response:
            raise InvalidServerResponseException(response)

    def create_wallet(self) -> Tuple[str, str]:
        response: dict = self.microservice("currency", ["create"], {})
        if "error" in response:
            error: str = response["error"]
            if error == "You already own a wallet!":
                raise AlreadyOwnAWalletException()
            raise InvalidServerResponseException(response)
        if "key" not in response or "uuid" not in response:
            raise InvalidServerResponseException(response)
        return response["uuid"], response["key"]

    def get_wallet(self, wallet_uuid: str, key: str) -> dict:
        response: dict = self.microservice("currency", ["get"], {
            "source_uuid": wallet_uuid,
            "key": key
        })
        if "error" in response:
            error: str = response["error"]
            if error == "invalid key":
                raise InvalidKeyException()
            raise InvalidServerResponseException(response)
        if "success" not in response:
            raise InvalidServerResponseException(response)
        return response["success"]

    def delete_wallet(self, wallet_uuid: str, key: str):
        response: dict = self.microservice("currency", ["delete"], {
            "source_uuid": wallet_uuid,
            "key": key
        })
        if "error" in response:
            error: str = response["error"]
            if error == "invalid key":
                raise InvalidKeyException()
            raise InvalidServerResponseException(response)
        if "ok" not in response:
            raise InvalidServerResponseException(response)

    def send(self, wallet_uuid: str, key: str, destination: str, amount: int, usage: str):
        response: dict = self.microservice("currency", ["send"], {
            "source_uuid": wallet_uuid,
            "key": key,
            "send_amount": amount,
            "destination_uuid": destination,
            "usage": usage
        })
        if "error" in response:
            error: str = response["error"]
            if error == "The source wallet would make debt transaction canceled":
                raise SourceWalletTransactionDebtException()
            if error.startswith("Your Souce or Destination uuid is invalid"):
                raise InvalidWalletException()
            if error == "invalid key":
                raise InvalidKeyException()
            raise InvalidServerResponseException(response)

    def create_service(self, device_uuid: str, name: str) -> dict:
        response: dict = self.microservice("service", ["create"], {
            "name": name,
            "device_uuid": device_uuid
        })
        if "error" in response:
            error: str = response["error"]
            if error == "you already own a service with this name":
                raise AlreadyOwnServiceException()
            raise InvalidServerResponseException(response)
        return response

    def get_services(self, device_uuid: str) -> List[dict]:
        response: dict = self.microservice("service", ["list"], {
            "device_uuid": device_uuid
        })
        if "error" in response or "services" not in response:
            raise InvalidServerResponseException(response)
        return response["services"]

    def use_service(self, device_uuid, service_uuid: str, **kwargs):
        response: dict = self.microservice("service", ["use"], {
            "device_uuid": device_uuid,
            "service_uuid": service_uuid,
            **kwargs
        })
        if "error" in response:
            error: str = response["error"]
            if error == "unknown service":
                raise UnknownServiceException()
            raise InvalidServerResponseException(response)
        return response

    def spot(self) -> dict:
        response: dict = self.microservice("device", ["device", "spot"], {})
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def device_info(self, device_uuid: str) -> dict:
        response: dict = self.microservice("device", ["device", "info"], {
            "device_uuid": device_uuid
        })
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def part_owner(self, device_uuid: str) -> bool:
        response: dict = self.microservice("service", ["part_owner"], {
            "device_uuid": device_uuid
        })
        if "error" in response or "ok" not in response:
            raise InvalidServerResponseException(response)
        return response["ok"]
