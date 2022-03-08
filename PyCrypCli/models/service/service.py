from __future__ import annotations

from typing import Any, TypeVar, TYPE_CHECKING

from pydantic import Field

from .public_service import PublicService
from ...exceptions import ServiceNotFoundError

if TYPE_CHECKING:
    from ...client import Client

ServiceType = TypeVar("ServiceType", bound="Service")


class Service(PublicService):
    owner_uuid: str = Field(alias="owner")
    running: bool
    part_owner_uuid: str | None = Field(alias="part_owner")
    speed: float

    @staticmethod
    def get_services(client: Client, device_uuid: str) -> list[Service]:
        return [
            Service.parse(client, service)
            for service in client.ms("service", ["list"], device_uuid=device_uuid)["services"]
        ]

    @staticmethod
    def get_service(client: Client, device_uuid: str, service_uuid: str) -> Service:
        return Service.parse(
            client, client.ms("service", ["private_info"], device_uuid=device_uuid, service_uuid=service_uuid)
        )

    @staticmethod
    def get_service_by_name(client: Client, device_uuid: str, name: str) -> Service:
        for service in Service.get_services(client, device_uuid):
            if service.name == name:
                return service
        raise ServiceNotFoundError

    @staticmethod
    def list_part_owner(client: Client) -> list[Service]:
        return [Service.parse(client, service) for service in client.ms("service", ["list_part_owner"])["services"]]

    def update(self) -> Service:
        return self._update(Service.get_service(self._client, self.device_uuid, self.uuid))

    def use(self, **data: Any) -> dict[Any, Any]:
        return self._ms("service", ["use"], device_uuid=self.device_uuid, service_uuid=self.uuid, **data)

    def toggle(self) -> Service:
        return self._update(self._ms("service", ["toggle"], device_uuid=self.device_uuid, service_uuid=self.uuid))

    def delete(self) -> None:
        self._ms("service", ["delete"], device_uuid=self.device_uuid, service_uuid=self.uuid)
