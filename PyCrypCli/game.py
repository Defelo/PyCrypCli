import re
import time
from typing import List, Optional, Tuple

from pypresence import Presence, PyPresenceException

from .client import Client
from .exceptions import FileNotFoundException, InvalidWalletFile
from .game_objects import Device, File, Wallet, Service
from .util import extract_wallet


class Game:
    def __init__(self, server: str):
        self.client: Client = Client(server)
        self.session_token: Optional[str] = None
        self.host: str = re.match(r"^wss?://(.+)$", server).group(1).split("/")[0]

        self.username: Optional[str] = None
        self.user_uuid: Optional[str] = None
        self.login_stack: List[Device] = []

        self.last_portscan: Optional[Tuple[str, List[Service]]] = None

        self.login_time: Optional[int] = None
        self.startup_time: int = int(time.time())

        self.presence: Presence = Presence(client_id="596676243144048640")
        try:
            self.presence.connect()
        except FileNotFoundError:
            self.presence = None

    def is_logged_in(self):
        return self.client.logged_in

    def update_presence(
        self,
        state: str = None,
        details: str = None,
        start: int = None,
        end: int = None,
        large_image: str = None,
        large_text: str = None,
    ):
        if self.presence is None:
            return
        try:
            self.presence.update(
                state=state, details=details, start=start, end=end, large_image=large_image, large_text=large_text
            )
        except PyPresenceException:
            pass

    def main_loop_presence(self):
        self.update_presence(
            state=f"Logged in: {self.username}@{self.host}",
            details="in Cryptic Terminal",
            start=self.startup_time,
            large_image="cryptic",
            large_text="Cryptic",
        )

    def login_loop_presence(self):
        self.update_presence(
            state=f"Server: {self.host}",
            details="Logging in",
            start=self.startup_time,
            large_image="cryptic",
            large_text="Cryptic",
        )

    def update_username(self):
        result: dict = self.client.info()
        self.username: str = result["name"]
        self.user_uuid: str = result["uuid"]

    def update_host(self):
        if self.login_stack:
            self.login_stack[-1] = self.client.device_info(self.login_stack[-1].uuid)

    def get_device(self) -> Device:
        assert self.login_stack

        return self.login_stack[-1]

    def is_local_device(self) -> bool:
        assert self.login_stack

        return self.user_uuid == self.get_device().owner

    def get_hacked_devices(self) -> List[Device]:
        return list({self.client.device_info(service.device) for service in self.client.list_part_owner()})

    def get_file(self, filename: str) -> Optional[File]:
        files: List[File] = self.client.get_files(self.get_device().uuid)
        for file in files:
            if file.filename == filename:
                return file
        return None

    def get_filenames(self) -> List[str]:
        return [file.filename for file in self.client.get_files(self.get_device().uuid)]

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
        services: List[Service] = self.client.get_services(self.get_device().uuid)
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
