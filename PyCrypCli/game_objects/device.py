from typing import List, Optional

from PyCrypCli.client import Client
from PyCrypCli.game_objects.device_hardware import DeviceHardware
from PyCrypCli.game_objects.file import File
from PyCrypCli.game_objects.game_object import GameObject
from PyCrypCli.game_objects.network import Network, NetworkInvitation
from PyCrypCli.game_objects.resource_usage import ResourceUsage
from PyCrypCli.game_objects.service import PublicService, Service, Miner


class Device(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def name(self) -> str:
        return self._data.get("name")

    @property
    def owner(self) -> str:
        return self._data.get("owner")

    @property
    def powered_on(self) -> bool:
        return self._data.get("powered_on")

    @staticmethod
    def get_device(client: Client, device_uuid: str) -> "Device":
        return Device(client, client.ms("device", ["device", "info"], device_uuid=device_uuid))

    @staticmethod
    def list_devices(client: Client) -> List["Device"]:
        return [Device(client, device) for device in client.ms("device", ["device", "all"])["devices"]]

    def update(self):
        self._update(Device.get_device(self._client, self.uuid))

    @staticmethod
    def build(client: Client, mainboard: str, cpu: str, gpu: str, ram: List[str], disk: List[str]) -> "Device":
        return Device(
            client,
            client.ms("device", ["device", "create"], motherboard=mainboard, cpu=cpu, gpu=gpu, ram=ram, disk=disk),
        )

    @staticmethod
    def starter_device(client: Client) -> "Device":
        return Device(client, client.ms("device", ["device", "starter_device"]))

    @staticmethod
    def spot(client: Client) -> "Device":
        return Device(client, client.ms("device", ["device", "spot"]))

    def power(self):
        self._update(self._ms("device", ["device", "power"], device_uuid=self.uuid))

    def change_name(self, name: str):
        self._update(self._ms("device", ["device", "change_name"], device_uuid=self.uuid, name=name))

    def delete(self):
        self._ms("device", ["device", "delete"], device_uuid=self.uuid)

    def get_files(self, parent_dir_uuid: Optional[str]) -> List[File]:
        return [
            File(self._client, file)
            for file in self._ms("device", ["file", "all"], device_uuid=self.uuid, parent_dir_uuid=parent_dir_uuid)[
                "files"
            ]
        ]

    def get_file(self, file_uuid: str) -> File:
        return File.get_file(self._client, self.uuid, file_uuid)

    def create_file(self, filename: str, content: str, is_directory: bool, parent_dir_uuid: Optional[str]) -> File:
        return File(
            self._client,
            self._ms(
                "device",
                ["file", "create"],
                device_uuid=self.uuid,
                filename=filename,
                content=content,
                is_directory=is_directory,
                parent_dir_uuid=parent_dir_uuid,
            ),
        )

    def get_public_service(self, service_uuid: str) -> PublicService:
        return PublicService.get_public_service(self._client, self.uuid, service_uuid)

    def get_services(self) -> List[Service]:
        return Service.get_services(self._client, self.uuid)

    def get_service(self, service_uuid: str) -> Service:
        return Service.get_service(self._client, self.uuid, service_uuid)

    def get_service_by_name(self, service: str) -> Service:
        return Service.get_service_by_name(self._client, self.uuid, service)

    def get_miner(self) -> Miner:
        return Miner.get_miner(self._client, self.uuid)

    def create_service(self, name: str, **extra) -> Service:
        return Service(self._client, self._ms("service", ["create"], name=name, device_uuid=self.uuid, **extra))

    def part_owner(self) -> bool:
        return self._ms("service", ["part_owner"], device_uuid=self.uuid)["ok"]

    def get_hardware(self) -> List[DeviceHardware]:
        return [
            DeviceHardware(self._client, dh)
            for dh in self._ms("device", ["device", "info"], device_uuid=self.uuid)["hardware"]
        ]

    def get_resource_usage(self) -> ResourceUsage:
        return ResourceUsage(self._client, self._ms("device", ["hardware", "resources"], device_uuid=self.uuid))

    def get_networks(self) -> List[Network]:
        return [Network(self._client, net) for net in self._ms("network", ["member"], device=self.uuid)["networks"]]

    def create_network(self, name: str, hidden: bool) -> Network:
        return Network(self._client, self._ms("network", ["create"], device=self.uuid, name=name, hidden=hidden))

    def get_network_invitations(self) -> List[NetworkInvitation]:
        return [
            NetworkInvitation(self._client, invitation)
            for invitation in self._ms("network", ["invitations"], device=self.uuid)["invitations"]
        ]
