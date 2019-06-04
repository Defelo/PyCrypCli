from typing import List, Optional

from client import Client


class Game:
    def __init__(self, server: str):
        self.client: Client = Client(server)
        self.session_token: str = None

        self.device_uuid: str = None
        self.hostname: str = None
        self.username: str = None

    def update_username(self):
        self.username: str = self.client.info()["name"]

    def update_host(self, device_uuid: str = None):
        if device_uuid is None:
            devices: List[dict] = self.client.get_all_devices()
            if not devices:
                devices: List[dict] = [self.client.create_device()]
            self.hostname: str = devices[0]["name"]
            self.device_uuid: str = devices[0]["uuid"]
        else:
            self.device_uuid: str = device_uuid
            self.hostname: str = self.client.device_info(device_uuid)["name"]

    def get_file(self, filename: str) -> Optional[dict]:
        files: List[dict] = self.client.get_all_files(self.device_uuid)
        for file in files:
            if file["filename"] == filename:
                return file
        return None

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
