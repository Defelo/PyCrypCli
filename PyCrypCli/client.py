import time
from typing import List, Optional
from uuid import uuid4

from websocket import WebSocket, create_connection

from .exceptions import *
from .game_objects import Device, File, Wallet, Service, Miner
from .timer import Timer


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
        self.websocket: WebSocket = create_connection(self.server)
        self.timer: Timer = Timer(10, self.info)

    def close(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

        self.websocket.close()
        self.websocket = None
        self.logged_in: bool = False

    def request(self, command: dict, no_response: bool = False) -> dict:
        assert self.websocket
        while self.waiting_for_response:
            time.sleep(0.01)
        self.waiting_for_response: bool = True
        self.websocket.send(json.dumps(command))
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

    def microservice(self, ms: str, endpoint: List[str], data: dict, *, ignore_errors=False) -> dict:
        assert self.logged_in

        response: dict = self.request({"ms": ms, "endpoint": endpoint, "data": data, "tag": uuid()})

        if "error" in response:
            error: str = response["error"]
            if error == "unknown microservice":
                raise UnknownMicroserviceException(ms)
            raise InvalidServerResponseException(response)

        if "data" not in response:
            raise InvalidServerResponseException(response)

        data: dict = response["data"]
        if "error" in data and not ignore_errors:
            error: str = data["error"]
            for exception in MicroserviceException.__subclasses__():  # type: MicroserviceException
                if exception.error == error:
                    raise exception
            raise InvalidServerResponseException(data)
        return data

    def register(self, username: str, email: str, password: str) -> str:
        assert not self.logged_in

        self.init()
        response: dict = self.request({"action": "register", "name": username, "mail": email, "password": password})
        if "error" in response:
            self.close()
            error: str = response["error"]
            if error == "invalid password":
                raise WeakPasswordException()
            if error == "username already exists":
                raise UsernameAlreadyExistsException()
            if error == "invalid email":
                raise InvalidEmailException()
            raise InvalidServerResponseException(response)
        if "token" not in response:
            self.close()
            raise InvalidServerResponseException(response)
        self.logged_in: bool = True
        self.timer.start()
        return response["token"]

    def login(self, username: str, password: str) -> str:
        assert not self.logged_in

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
        assert not self.logged_in

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
        assert not self.logged_in

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
        assert self.logged_in

        self.close()

    def status(self) -> dict:
        assert not self.logged_in

        self.init()
        response: dict = self.request({"action": "status"})
        self.close()
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def info(self) -> dict:
        assert self.logged_in

        response: dict = self.request({"action": "info"})
        if "error" in response:
            raise InvalidServerResponseException(response)
        return response

    def delete_user(self):
        assert self.logged_in

        self.request({"action": "delete"}, no_response=True)
        self.close()

    def get_devices(self) -> List[Device]:
        return [Device.deserialize(device) for device in self.microservice("device", ["device", "all"], {})["devices"]]

    # def create_device(self) -> Device:
    #     return Device.deserialize(self.microservice("device", ["device", "create"], {}))

    def create_starter_device(self) -> Device:
        return Device.deserialize(self.microservice("device", ["device", "starter_device"], {}))

    def change_device_name(self, device_uuid: str, name: str):
        self.microservice("device", ["device", "change_name"], {"device_uuid": device_uuid, "name": name})

    def get_files(self, device_uuid: str) -> List[File]:
        return [
            File.deserialize(file)
            for file in self.microservice("device", ["file", "all"], {"device_uuid": device_uuid})["files"]
        ]

    def create_file(self, device_uuid: str, filename: str, content: str) -> File:
        return File.deserialize(
            self.microservice(
                "device", ["file", "create"], {"device_uuid": device_uuid, "filename": filename, "content": content}
            )
        )

    def device_info(self, device_uuid: str) -> Device:
        return Device.deserialize(self.microservice("device", ["device", "info"], {"device_uuid": device_uuid}))

    def file_move(self, device_uuid: str, file_uuid: str, new_filename: str) -> File:
        return File.deserialize(
            self.microservice(
                "device",
                ["file", "move"],
                {"device_uuid": device_uuid, "file_uuid": file_uuid, "filename": new_filename},
            )
        )

    def file_update(self, device_uuid: str, file_uuid: str, new_content: str) -> File:
        return File.deserialize(
            self.microservice(
                "device",
                ["file", "update"],
                {"device_uuid": device_uuid, "file_uuid": file_uuid, "content": new_content},
            )
        )

    def remove_file(self, device_uuid: str, file_uuid: str):
        self.microservice("device", ["file", "delete"], {"device_uuid": device_uuid, "file_uuid": file_uuid})

    def create_wallet(self) -> Wallet:
        return Wallet.deserialize({**self.microservice("currency", ["create"], {}), "transactions": []})

    def get_wallet(self, wallet_uuid: str, key: str) -> Wallet:
        return Wallet.deserialize(self.microservice("currency", ["get"], {"source_uuid": wallet_uuid, "key": key}))

    def list_wallets(self) -> List[str]:
        return self.microservice("currency", ["list"], {})["wallets"]

    def reset_wallet(self, wallet_uuid: str):
        self.microservice("currency", ["reset"], {"source_uuid": wallet_uuid})

    def delete_wallet(self, wallet: Wallet):
        self.microservice("currency", ["delete"], {"source_uuid": wallet.uuid, "key": wallet.key})

    def send(self, wallet: Wallet, destination: str, amount: int, usage: str):
        self.microservice(
            "currency",
            ["send"],
            {
                "source_uuid": wallet.uuid,
                "key": wallet.key,
                "send_amount": amount,
                "destination_uuid": destination,
                "usage": usage,
            },
        )

    def create_service(self, device_uuid: str, name: str, extra: dict) -> Service:
        return Service.deserialize(
            self.microservice("service", ["create"], {"name": name, "device_uuid": device_uuid, **extra})
        )

    def get_services(self, device_uuid: str) -> List[Service]:
        return [
            Service.deserialize(service)
            for service in self.microservice("service", ["list"], {"device_uuid": device_uuid})["services"]
        ]

    def use_service(self, device_uuid, service_uuid: str, **kwargs) -> dict:
        return self.microservice(
            "service", ["use"], {"device_uuid": device_uuid, "service_uuid": service_uuid, **kwargs}
        )

    def bruteforce_attack(self, device_uuid: str, service_uuid: str, target_device: str, target_service: str) -> dict:
        return self.microservice(
            "service",
            ["bruteforce", "attack"],
            {
                "device_uuid": device_uuid,
                "service_uuid": service_uuid,
                "target_device": target_device,
                "target_service": target_service,
            },
        )

    def bruteforce_status(self, device_uuid: str, service_uuid: str) -> dict:
        try:
            return {
                "running": True,
                **self.microservice(
                    "service", ["bruteforce", "status"], {"device_uuid": device_uuid, "service_uuid": service_uuid}
                ),
            }
        except AttackNotRunningException:
            return {"running": False}

    def bruteforce_stop(self, device_uuid: str, service_uuid: str) -> dict:
        return self.microservice(
            "service", ["bruteforce", "stop"], {"device_uuid": device_uuid, "service_uuid": service_uuid}
        )

    def spot(self) -> Device:
        return Device.deserialize(self.microservice("device", ["device", "spot"], {}))

    def part_owner(self, device_uuid: str) -> bool:
        return self.microservice("service", ["part_owner"], {"device_uuid": device_uuid})["ok"]

    def list_part_owner(self) -> List[Service]:
        return [
            Service.deserialize(service)
            for service in self.microservice("service", ["list_part_owner"], {})["services"]
        ]

    def get_miner(self, service_uuid: str) -> Miner:
        return Miner.deserialize(self.microservice("service", ["miner", "get"], {"service_uuid": service_uuid}))

    def miner_power(self, service_uuid: str, power: float):
        self.microservice("service", ["miner", "power"], {"service_uuid": service_uuid, "power": power})

    def miner_wallet(self, service_uuid: str, wallet_uuid: str):
        self.microservice("service", ["miner", "wallet"], {"service_uuid": service_uuid, "wallet_uuid": wallet_uuid})

    def delete_service(self, device_uuid: str, service_uuid: str):
        self.microservice("service", ["delete"], {"device_uuid": device_uuid, "service_uuid": service_uuid})
