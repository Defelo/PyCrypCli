from __future__ import annotations

from typing import Any, cast, TYPE_CHECKING

from pydantic import Field

from .device_hardware import DeviceHardware
from .file import File
from .model import Model
from .network import Network, NetworkInvitation
from .resource_usage import ResourceUsage
from .service import PublicService, Service, Miner

if TYPE_CHECKING:
    from ..client import Client


class Device(Model):
    uuid: str
    name: str
    owner_uuid: str = Field(alias="owner")
    powered_on: bool

    def __hash__(self) -> int:
        return hash(self.uuid)

    @staticmethod
    def get_device(client: Client, device_uuid: str) -> Device:
        return Device.parse(client, client.ms("device", ["device", "info"], device_uuid=device_uuid))

    @staticmethod
    def list_devices(client: Client) -> list[Device]:
        return [Device.parse(client, device) for device in client.ms("device", ["device", "all"])["devices"]]

    def update(self) -> Device:
        return self._update(Device.get_device(self._client, self.uuid))

    @staticmethod
    def build(client: Client, mainboard: str, cpu: str, gpu: str, ram: list[str], disk: list[str]) -> Device:
        return Device.parse(
            client,
            client.ms("device", ["device", "create"], motherboard=mainboard, cpu=cpu, gpu=gpu, ram=ram, disk=disk),
        )

    @staticmethod
    def starter_device(client: Client) -> Device:
        return Device.parse(client, client.ms("device", ["device", "starter_device"]))

    @staticmethod
    def spot(client: Client) -> Device:
        return Device.parse(client, client.ms("device", ["device", "spot"]))

    def power(self) -> Device:
        return self._update(self._ms("device", ["device", "power"], device_uuid=self.uuid))

    def change_name(self, name: str) -> Device:
        return self._update(self._ms("device", ["device", "change_name"], device_uuid=self.uuid, name=name))

    def delete(self) -> None:
        self._ms("device", ["device", "delete"], device_uuid=self.uuid)

    def get_files(self, parent_dir_uuid: str | None) -> list[File]:
        return [
            File.parse(self._client, file)
            for file in self._ms("device", ["file", "all"], device_uuid=self.uuid, parent_dir_uuid=parent_dir_uuid)[
                "files"
            ]
        ]

    def get_file(self, file_uuid: str) -> File:
        return File.get_file(self._client, self.uuid, file_uuid)

    def create_file(self, filename: str, content: str, is_directory: bool, parent_dir_uuid: str | None) -> File:
        return File.parse(
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

    def get_services(self) -> list[Service]:
        return Service.get_services(self._client, self.uuid)

    def get_service(self, service_uuid: str) -> Service:
        return Service.get_service(self._client, self.uuid, service_uuid)

    def get_service_by_name(self, service: str) -> Service:
        return Service.get_service_by_name(self._client, self.uuid, service)

    def get_miner(self) -> Miner:
        return Miner.get_miner(self._client, self.uuid)

    def create_service(self, name: str, **extra: Any) -> Service:
        return Service.parse(self._client, self._ms("service", ["create"], name=name, device_uuid=self.uuid, **extra))

    def part_owner(self) -> bool:
        return cast(bool, self._ms("service", ["part_owner"], device_uuid=self.uuid)["ok"])

    def get_hardware(self) -> list[DeviceHardware]:
        return [
            DeviceHardware.parse(self._client, dh)
            for dh in self._ms("device", ["device", "info"], device_uuid=self.uuid)["hardware"]
        ]

    def get_resource_usage(self) -> ResourceUsage:
        return ResourceUsage.parse(self._client, self._ms("device", ["hardware", "resources"], device_uuid=self.uuid))

    def get_networks(self) -> list[Network]:
        return [
            Network.parse(self._client, net) for net in self._ms("network", ["member"], device=self.uuid)["networks"]
        ]

    def create_network(self, name: str, hidden: bool) -> Network:
        return Network.parse(self._client, self._ms("network", ["create"], device=self.uuid, name=name, hidden=hidden))

    def get_network_invitations(self) -> list[NetworkInvitation]:
        return [
            NetworkInvitation.parse(self._client, invitation)
            for invitation in self._ms("network", ["invitations"], device=self.uuid)["invitations"]
        ]
