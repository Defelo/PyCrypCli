import json
import re
import ssl
import time
from typing import List, Optional, Type
from uuid import uuid4

from websocket import WebSocket, create_connection

from PyCrypCli.exceptions import (
    UnknownMicroserviceException,
    InvalidServerResponseException,
    MicroserviceException,
    WeakPasswordException,
    UsernameAlreadyExistsException,
    InvalidLoginException,
    InvalidSessionTokenException,
    PermissionsDeniedException,
    LoggedInException,
    LoggedOutException,
)
from PyCrypCli.timer import Timer


def uuid() -> str:
    return str(uuid4())


class Client:
    def __init__(self, server: str):
        self.server: str = server
        self.websocket: Optional[WebSocket] = None
        self.timer: Optional[Timer] = None
        self.waiting_for_response: bool = False
        self.notifications: List[dict] = []
        self.logged_in: bool = False

    def init(self):
        try:
            self.websocket: WebSocket = create_connection(self.server)
        except ssl.SSLCertVerificationError:
            self.websocket: WebSocket = create_connection(self.server, sslopt={"cert_reqs": ssl.CERT_NONE})
        self.timer: Timer = Timer(10, self.info)

    def close(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

        self.websocket.close()
        self.websocket = None
        self.logged_in: bool = False

    def request(self, data: dict, no_response: bool = False) -> dict:
        if self.websocket is None:
            raise ConnectionError

        while self.waiting_for_response:
            time.sleep(0.01)
        self.waiting_for_response: bool = True
        self.websocket.send(json.dumps(data))
        if no_response:
            self.waiting_for_response: bool = False
            return {}
        while True:
            response: dict = json.loads(self.websocket.recv())
            if "notify-id" in response:
                self.notifications.append(response)
            else:
                break
        self.waiting_for_response: bool = False
        return response

    def ms(self, ms: str, endpoint: List[str], **data) -> dict:
        if not self.logged_in:
            raise LoggedOutException

        response: dict = self.request({"ms": ms, "endpoint": endpoint, "data": data, "tag": uuid()})

        if "error" in response:
            error: str = response["error"]
            if error == "unknown microservice":
                raise UnknownMicroserviceException(ms)
            raise InvalidServerResponseException(response)

        if "data" not in response:
            raise InvalidServerResponseException(response)

        data: dict = response["data"]
        if "error" in data:
            error: str = data["error"]
            for exception in MicroserviceException.__subclasses__():  # type: Type[MicroserviceException]
                match = re.fullmatch(exception.error, error)
                if match:
                    raise exception(error, list(match.groups()))
            raise InvalidServerResponseException(response)
        return data

    def register(self, username: str, password: str) -> str:
        if self.logged_in:
            raise LoggedInException

        self.init()
        response: dict = self.request({"action": "register", "name": username, "password": password})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "invalid password":
                raise WeakPasswordException()
            if error == "username already exists":
                raise UsernameAlreadyExistsException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.logged_in: bool = True
        self.timer.start()
        return response["token"]

    def login(self, username: str, password: str) -> str:
        if self.logged_in:
            raise LoggedInException

        self.init()
        response: dict = self.request({"action": "login", "name": username, "password": password})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "permissions denied":
                raise InvalidLoginException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.logged_in: bool = True
        self.timer.start()
        return response["token"]

    def session(self, token: str):
        if self.logged_in:
            raise LoggedInException

        self.init()
        response: dict = self.request({"action": "session", "token": token})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "invalid token":
                raise InvalidSessionTokenException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.logged_in: bool = True
        self.timer.start()

    def change_password(self, username: str, old_password: str, new_password: str):
        if self.logged_in:
            raise LoggedInException

        self.init()
        response: dict = self.request(
            {"action": "password", "name": username, "password": old_password, "new": new_password}
        )
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "permissions denied":
                raise PermissionsDeniedException()
        self.close()

    def logout(self):
        if not self.logged_in:
            raise LoggedOutException

        self.request({"action": "logout"})
        self.close()

    def status(self) -> dict:
        if self.logged_in:
            raise LoggedInException

        self.init()
        response: dict = self.request({"action": "status"})
        self.close()
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def info(self) -> dict:
        if not self.logged_in:
            raise LoggedOutException

        response: dict = self.request({"action": "info"})
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def delete_user(self):
        if not self.logged_in:
            raise LoggedOutException

        self.request({"action": "delete"}, no_response=True)
        self.close()

    def get_hardware_config(self) -> dict:
        return self.ms("device", ["hardware", "list"])
