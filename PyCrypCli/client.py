import ssl
import time
from typing import List, Optional, Tuple, Dict
from uuid import uuid4

from websocket import WebSocket, create_connection

from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import (
    Device,
    File,
    Wallet,
    Service,
    Miner,
    InventoryElement,
    ShopProduct,
    ResourceUsage,
    DeviceHardware,
    Network,
    NetworkMembership,
    NetworkInvitation,
    Transaction,
    ShopCategory,
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
            raise InvalidServerResponseException(response)
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

        self.request({"action": "logout"})
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

    def build_device(self, mainboard: str, cpu: str, gpu: str, ram: List[str], disk: List[str]) -> Device:
        return Device.deserialize(
            self.microservice(
                "device",
                ["device", "create"],
                {"motherboard": mainboard, "cpu": cpu, "gpu": gpu, "ram": ram, "disk": disk},
            )
        )

    def create_starter_device(self) -> Device:
        return Device.deserialize(self.microservice("device", ["device", "starter_device"], {}))

    def device_power(self, device_uuid: str) -> Device:
        return Device.deserialize(self.microservice("device", ["device", "power"], {"device_uuid": device_uuid}))

    def get_hardware_config(self) -> dict:
        return self.microservice("device", ["hardware", "list"], {})

    def change_device_name(self, device_uuid: str, name: str):
        self.microservice("device", ["device", "change_name"], {"device_uuid": device_uuid, "name": name})

    def delete_device(self, device_uuid: str):
        self.microservice("device", ["device", "delete"], {"device_uuid": device_uuid})

    def get_files(self, device_uuid: str, parent_dir_uuid: Optional[str]) -> List[File]:
        return [
            File.deserialize(file)
            for file in self.microservice(
                "device", ["file", "all"], {"device_uuid": device_uuid, "parent_dir_uuid": parent_dir_uuid}
            )["files"]
        ]

    def get_file(self, device_uuid: str, file_uuid: str) -> File:
        return File.deserialize(
            self.microservice("device", ["file", "info"], {"device_uuid": device_uuid, "file_uuid": file_uuid})
        )

    def create_file(
        self, device_uuid: str, filename: str, content: str, is_directory: bool, parent_dir_uuid: Optional[str]
    ) -> File:
        return File.deserialize(
            self.microservice(
                "device",
                ["file", "create"],
                {
                    "device_uuid": device_uuid,
                    "filename": filename,
                    "content": content,
                    "is_directory": is_directory,
                    "parent_dir_uuid": parent_dir_uuid,
                },
            )
        )

    def device_info(self, device_uuid: str) -> Device:
        return Device.deserialize(self.microservice("device", ["device", "info"], {"device_uuid": device_uuid}))

    def file_move(self, device_uuid: str, file_uuid: str, new_filename: str, new_parent_dir_uuid: str) -> File:
        return File.deserialize(
            self.microservice(
                "device",
                ["file", "move"],
                {
                    "device_uuid": device_uuid,
                    "file_uuid": file_uuid,
                    "new_filename": new_filename,
                    "new_parent_dir_uuid": new_parent_dir_uuid,
                },
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

    def get_transactions(self, wallet: Wallet, count: int, offset: int) -> List[Transaction]:
        return [
            Transaction.deserialize(t)
            for t in self.microservice(
                "currency",
                ["transactions"],
                {"source_uuid": wallet.uuid, "key": wallet.key, "count": count, "offset": offset},
            )["transactions"]
        ]

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

    def use_service(self, device_uuid: str, service_uuid: str, **kwargs) -> dict:
        return self.microservice(
            "service", ["use"], {"device_uuid": device_uuid, "service_uuid": service_uuid, **kwargs}
        )

    def toggle_service(self, device_uuid: str, service_uuid: str) -> Service:
        return Service.deserialize(
            self.microservice("service", ["toggle"], {"device_uuid": device_uuid, "service_uuid": service_uuid})
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

    def get_miners(self, wallet_uuid: str) -> List[Tuple[Miner, Service]]:
        return [
            (Miner.deserialize(miner["miner"]), Service.deserialize(miner["service"]))
            for miner in self.microservice("service", ["miner", "list"], {"wallet_uuid": wallet_uuid})["miners"]
        ]

    def miner_power(self, service_uuid: str, power: float):
        self.microservice("service", ["miner", "power"], {"service_uuid": service_uuid, "power": power})

    def miner_wallet(self, service_uuid: str, wallet_uuid: str):
        self.microservice("service", ["miner", "wallet"], {"service_uuid": service_uuid, "wallet_uuid": wallet_uuid})

    def delete_service(self, device_uuid: str, service_uuid: str):
        self.microservice("service", ["delete"], {"device_uuid": device_uuid, "service_uuid": service_uuid})

    def inventory_list(self) -> List[InventoryElement]:
        return [
            InventoryElement.deserialize(element)
            for element in self.microservice("inventory", ["inventory", "list"], {})["elements"]
        ]

    def shop_list(self) -> List[ShopCategory]:
        out = [
            ShopCategory.deserialize({"name": k, **v})
            for k, v in self.microservice("inventory", ["shop", "list"], {})["categories"].items()
        ]
        out.sort(key=lambda c: c.index)
        return out

    def shop_info(self, product: str) -> ShopProduct:
        return ShopProduct.deserialize(self.microservice("inventory", ["shop", "info"], {"product": product}))

    def shop_buy(self, products: Dict[str, int], wallet_uuid: str, key: str) -> List[InventoryElement]:
        return [
            InventoryElement.deserialize(element)
            for element in self.microservice(
                "inventory", ["shop", "buy"], {"products": products, "wallet_uuid": wallet_uuid, "key": key}
            )["bought_products"]
        ]

    def inventory_trade(self, element_uuid: str, target: str):
        self.microservice("inventory", ["inventory", "trade"], {"element_uuid": element_uuid, "target": target})

    def hardware_resources(self, device_uuid: str) -> ResourceUsage:
        return ResourceUsage.deserialize(
            self.microservice("device", ["hardware", "resources"], {"device_uuid": device_uuid})
        )

    def get_device_hardware(self, device_uuid: str) -> List[DeviceHardware]:
        return [
            DeviceHardware.deserialize(dh)
            for dh in self.microservice("device", ["device", "info"], {"device_uuid": device_uuid})["hardware"]
        ]

    def get_networks(self, device: str) -> List[Network]:
        return [
            Network.deserialize(net) for net in self.microservice("network", ["member"], {"device": device})["networks"]
        ]

    def get_public_networks(self) -> List[Network]:
        return [Network.deserialize(net) for net in self.microservice("network", ["public"], {})["networks"]]

    def create_network(self, device: str, name: str, hidden: bool) -> Network:
        return Network.deserialize(
            self.microservice("network", ["create"], {"device": device, "name": name, "hidden": hidden})
        )

    def get_network_by_uuid(self, network_uuid: str) -> Network:
        return Network.deserialize(self.microservice("network", ["get"], {"uuid": network_uuid}))

    def get_network_by_name(self, name: str) -> Network:
        return Network.deserialize(self.microservice("network", ["name"], {"name": name}))

    def get_members_of_network(self, network: str) -> List[NetworkMembership]:
        return [
            NetworkMembership.deserialize(member)
            for member in self.microservice("network", ["members"], {"uuid": network})["members"]
        ]

    def request_network_membership(self, network: str, device: str) -> NetworkInvitation:
        return NetworkInvitation.deserialize(
            self.microservice("network", ["request"], {"uuid": network, "device": device})
        )

    def get_network_membership_requests(self, network: str) -> List[NetworkInvitation]:
        return [
            NetworkInvitation.deserialize(invitation)
            for invitation in self.microservice("network", ["requests"], {"uuid": network})["requests"]
        ]

    def get_network_invitations(self, device: str) -> List[NetworkInvitation]:
        return [
            NetworkInvitation.deserialize(invitation)
            for invitation in self.microservice("network", ["invitations"], {"device": device})["invitations"]
        ]

    def invite_to_network(self, device: str, network: str) -> NetworkInvitation:
        return NetworkInvitation.deserialize(
            self.microservice("network", ["invite"], {"uuid": network, "device": device})
        )

    def accept_network_membership_request(self, request: str):
        self.microservice("network", ["accept"], {"uuid": request})

    def deny_network_membership_request(self, request: str):
        self.microservice("network", ["deny"], {"uuid": request})

    def leave_network(self, device: str, network: str):
        self.microservice("network", ["leave"], {"uuid": network, "device": device})

    def kick_from_network(self, device: str, network: str):
        self.microservice("network", ["kick"], {"uuid": network, "device": device})

    def delete_network(self, network: str):
        self.microservice("network", ["delete"], {"uuid": network})
