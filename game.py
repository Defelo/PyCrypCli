import re
from typing import List, Optional, Tuple

from pypresence import Presence

from client import Client
from exceptions import FileNotFoundException, InvalidWalletFile
from game_objects import Device, File, Wallet, Service
from util import extract_wallet


class Game:
    def __init__(self, server: str):
        self.client: Client = Client(server)
        self.session_token: str = None
        self.host: str = re.match(r"^wss?://(.+)$", server).group(1).split("/")[0]

        self.device_uuid: str = None
        self.hostname: str = None
        self.username: str = None

        self.last_portscan: Tuple[str, List[Service]] = None

        self.login_time: int = None

        self.presence: Presence = Presence(client_id="596676243144048640")
        self.presence.connect()

    def main_loop_presence(self):
        self.presence.update(state=f"Logged in: {self.username}@{self.host}", details="in Cryptic Terminal",
                             start=self.login_time, large_image="cryptic", large_text="Cryptic")

    def update_username(self):
        self.username: str = self.client.info()["name"]

    def update_host(self, device_uuid: str = None):
        if device_uuid is None:
            devices: List[Device] = self.client.get_devices()
            if not devices:
                devices: List[Device] = [self.client.create_device()]
            self.hostname: str = devices[0].name
            self.device_uuid: str = devices[0].uuid
        else:
            self.device_uuid: str = device_uuid
            self.hostname: str = self.client.device_info(device_uuid).name

    def get_file(self, filename: str) -> Optional[File]:
        files: List[File] = self.client.get_files(self.device_uuid)
        for file in files:
            if file.filename == filename:
                return file
        return None

    def get_wallet_from_file(self, filename: str) -> Wallet:
        file: File = self.get_file(filename)
        if file is None:
            raise FileNotFoundException

        return self.extract_wallet(file.content)

    def extract_wallet(self, content: str) -> Wallet:
        wallet = extract_wallet(content)
        if wallet is None:
            raise InvalidWalletFile
        return self.client.get_wallet(*wallet)

    def get_service(self, name: str) -> Optional[Service]:
        services: List[Service] = self.client.get_services(self.device_uuid)
        for service in services:
            if service.name == name:
                return service
        return None

    def ask(self, prompt: str, options: List[str]) -> str:
        pass

    def remote_login(self, uuid: str):
        pass

    def update_last_portscan(self, scan: Tuple[str, List[Service]]):
        self.last_portscan: Tuple[str, List[Service]] = scan

    def get_last_portscan(self) -> Tuple[str, List[Service]]:
        return self.last_portscan
