import json
import re
import ssl
import time
from os import getenv
from typing import Type, Any, cast
from uuid import uuid4

import sentry_sdk
from pydantic import ValidationError
from websocket import WebSocket, create_connection

from .exceptions import (
    UnknownMicroserviceError,
    InvalidServerResponseError,
    MicroserviceException,
    WeakPasswordError,
    UsernameAlreadyExistsError,
    InvalidLoginError,
    InvalidSessionTokenError,
    PermissionDeniedError,
    LoggedInError,
    LoggedOutError,
    ClientNotReadyError,
)
from .models import HardwareConfig, StatusResponse, InfoResponse, TokenResponse
from .timer import Timer

LOG_WS = bool(getenv("LOG_WS"))


def uuid() -> str:
    return str(uuid4())


class Client:
    def __init__(self, server: str):
        self.server: str = server
        self.websocket: WebSocket | None = None
        self.timer: Timer | None = None
        self.waiting_for_response: bool = False
        self.notifications: list[dict[str, Any]] = []
        self.logged_in: bool = False

    def init(self) -> None:
        try:
            self.websocket = create_connection(self.server)
        except ssl.SSLCertVerificationError:
            self.websocket = create_connection(self.server, sslopt={"cert_reqs": ssl.CERT_NONE})
        self.timer = Timer(10, self.info)

    def close(self) -> None:
        if self.timer:
            self.timer.stop()
            self.timer = None

        if self.websocket:
            self.websocket.close()
            self.websocket = None

        self.logged_in = False

    def _send(self, obj: dict[str, Any]) -> None:
        if not self.websocket:
            raise ClientNotReadyError

        data = json.dumps(obj)
        if LOG_WS:
            print("send:", data)
        sentry_sdk.add_breadcrumb(category="ws", message=f"send: {data}", level="debug")
        self.websocket.send(data)

    def _recv(self) -> dict[str, Any]:
        if not self.websocket:
            raise ClientNotReadyError

        data = self.websocket.recv()
        if LOG_WS:
            print("recv:", data)
        sentry_sdk.add_breadcrumb(category="ws", message=f"recv: {data}", level="debug")
        return cast(dict[str, Any], json.loads(data))

    def request(self, data: dict[str, Any], no_response: bool = False) -> dict[str, Any]:
        if self.websocket is None:
            raise ConnectionError

        while self.waiting_for_response:
            time.sleep(0.01)
        self.waiting_for_response = True

        self._send(data)

        if no_response:
            self.waiting_for_response = False
            return {}

        while True:
            response = self._recv()
            if "notify-id" in response:
                self.notifications.append(response)
            else:
                break

        self.waiting_for_response = False
        return response

    def ms(self, ms: str, endpoint: list[str], *, retry: int = 0, **data: Any) -> dict[str, Any]:
        if not self.logged_in:
            raise LoggedOutError

        response: dict[str, Any] = self.request({"ms": ms, "endpoint": endpoint, "data": data, "tag": uuid()})

        if "error" in response:
            error: str = response["error"]
            if error == "unknown microservice":
                raise UnknownMicroserviceError(ms)
            raise InvalidServerResponseError(response)

        if "data" not in response:
            raise InvalidServerResponseError(response)

        response_data: dict[str, Any] = response["data"]
        if "error" in response_data:
            error = response_data["error"]
            exception: Type[MicroserviceException]
            for exception in MicroserviceException.__subclasses__():
                if exception.error and (match := re.fullmatch(exception.error, error)):
                    raise exception(list(match.groups()))
            raise InvalidServerResponseError(response)

        if not response_data and retry:
            return self.ms(ms, endpoint, retry=retry - 1, **data)

        return response_data

    def register(self, username: str, password: str) -> TokenResponse:
        if self.logged_in:
            raise LoggedInError

        self.init()
        response: dict[str, Any] = self.request({"action": "register", "name": username, "password": password})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "invalid password":
                raise WeakPasswordError()
            if error == "username already exists":
                raise UsernameAlreadyExistsError()
            raise InvalidServerResponseError(response)

        try:
            token_response = TokenResponse.parse(self, response)
        except ValidationError:
            self.close()
            raise

        self.logged_in = True
        cast(Timer, self.timer).start()
        return token_response

    def login(self, username: str, password: str) -> TokenResponse:
        if self.logged_in:
            raise LoggedInError

        self.init()
        response: dict[str, Any] = self.request({"action": "login", "name": username, "password": password})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "permissions denied":
                raise InvalidLoginError()
            raise InvalidServerResponseError(response)

        try:
            token_response = TokenResponse.parse(self, response)
        except ValidationError:
            self.close()
            raise

        self.logged_in = True
        cast(Timer, self.timer).start()
        return token_response

    def session(self, token: str) -> TokenResponse:
        if self.logged_in:
            raise LoggedInError

        self.init()
        response: dict[str, Any] = self.request({"action": "session", "token": token})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "invalid token":
                raise InvalidSessionTokenError()
            raise InvalidServerResponseError(response)

        try:
            token_response = TokenResponse.parse(self, response)
        except ValidationError:
            self.close()
            raise

        self.logged_in = True
        cast(Timer, self.timer).start()
        return token_response

    def change_password(self, old_password: str, new_password: str) -> TokenResponse:
        if not self.logged_in:
            raise LoggedOutError

        response: dict[str, Any] = self.request({"action": "password", "password": old_password, "new": new_password})
        if "error" in response:
            error: str = response["error"]
            if error == "permissions denied":
                raise PermissionDeniedError
            raise InvalidServerResponseError(response)

        return TokenResponse.parse(self, response)

    def logout(self) -> None:
        if not self.logged_in:
            raise LoggedOutError

        self.request({"action": "logout"})
        self.close()

    def status(self) -> StatusResponse:
        if self.logged_in:
            raise LoggedInError

        self.init()
        response: dict[str, Any] = self.request({"action": "status"})
        self.close()
        if "error" in response:
            raise InvalidServerResponseError(response)
        return StatusResponse.parse(self, response)

    def info(self) -> InfoResponse:
        if not self.logged_in:
            raise LoggedOutError

        response: dict[str, Any] = self.request({"action": "info"})
        if "error" in response:
            raise InvalidServerResponseError(response)
        return InfoResponse.parse(self, response)

    def delete_user(self) -> None:
        if not self.logged_in:
            raise LoggedOutError

        self.request({"action": "delete"}, no_response=True)
        self.close()

    def get_hardware_config(self) -> HardwareConfig:
        return HardwareConfig.parse(self, self.ms("device", ["hardware", "list"]))
