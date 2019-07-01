from typing import List, Optional, Tuple

from client import Client
from util import extract_wallet


class Game:
    def __init__(self, server: str):
        self.client: Client = Client(server)
        self.session_token: str = None

        self.device_uuid: str = None
        self.hostname: str = None
        self.username: str = None

        self.last_portscan: Tuple[str, List[dict]] = None

    def update_username(self):
        self.username: str = self.client.info()["name"]

    def update_host(self, device_uuid: str = None):
        if device_uuid is None:
            devices: List[dict] = self.client.get_devices()
            if not devices:
                devices: List[dict] = [self.client.create_device()]
            self.hostname: str = devices[0]["name"]
            self.device_uuid: str = devices[0]["uuid"]
        else:
            self.device_uuid: str = device_uuid
            self.hostname: str = self.client.device_info(device_uuid)["name"]

    def get_file(self, filename: str) -> Optional[dict]:
        files: List[dict] = self.client.get_files(self.device_uuid)
        for file in files:
            if file["filename"] == filename:
                return file
        return None

    def get_wallet_from_file(self, filename: str) -> Optional[Tuple[str, str]]:
        file: dict = self.get_file(filename)
        if file is None:
            return None

        return extract_wallet(file["content"])

    def get_service(self, name: str) -> Optional[dict]:
        services: List[dict] = self.client.get_services(self.device_uuid)
        for service in services:
            if service["name"] == name:
                return service
        return None

    def ask(self, prompt: str, options: List[str]) -> str:
        pass

    def remote_login(self, uuid: str):
        pass

    def update_last_portscan(self, scan: Tuple[str, List[dict]]):
        self.last_portscan: Tuple[str, List[dict]] = scan

    def get_last_portscan(self) -> Tuple[str, List[dict]]:
        return self.last_portscan
