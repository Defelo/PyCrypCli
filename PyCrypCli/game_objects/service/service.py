from typing import List

from PyCrypCli.exceptions import ServiceNotFoundException

from PyCrypCli.client import Client
from PyCrypCli.game_objects.service.public_service import PublicService


class Service(PublicService):
    @property
    def owner(self) -> str:
        return self._data.get("owner")

    @property
    def running(self) -> bool:
        return self._data.get("running")

    @property
    def part_owner(self) -> str:
        return self._data.get("part_owner")

    @property
    def speed(self) -> float:
        return self._data.get("speed")

    @staticmethod
    def get_services(client: Client, device_uuid: str) -> List["Service"]:
        return [
            Service(client, service) for service in client.ms("service", ["list"], device_uuid=device_uuid)["services"]
        ]

    @staticmethod
    def get_service(client: Client, device_uuid: str, service_uuid: str) -> "Service":
        return Service(
            client, client.ms("service", ["private_info"], device_uuid=device_uuid, service_uuid=service_uuid)
        )

    @staticmethod
    def get_service_by_name(client: Client, device_uuid: str, name: str) -> "Service":
        for service in Service.get_services(client, device_uuid):
            if service.name == name:
                return service
        raise ServiceNotFoundException

    @staticmethod
    def list_part_owner(client: Client) -> List["Service"]:
        return [Service(client, service) for service in client.ms("service", ["list_part_owner"])["services"]]

    def update(self):
        self._update(Service.get_service(self._client, self.device, self.uuid))

    def use(self, **data) -> dict:
        return self._ms("service", ["use"], device_uuid=self.device, service_uuid=self.uuid, **data)

    def toggle(self):
        self._update(self._ms("service", ["toggle"], device_uuid=self.device, service_uuid=self.uuid))

    def delete(self):
        self._ms("service", ["delete"], device_uuid=self.device, service_uuid=self.uuid)
