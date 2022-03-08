from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from ..model import Model

if TYPE_CHECKING:
    from ...client import Client


class PublicService(Model):
    uuid: str
    device_uuid: str = Field(alias="device")
    name: str
    running_port: int | None

    @staticmethod
    def get_public_service(client: Client, device_uuid: str, service_uuid: str) -> PublicService:
        return PublicService.parse(
            client, client.ms("service", ["public_info"], device_uuid=device_uuid, service_uuid=service_uuid)
        )

    def update(self) -> PublicService:
        return self._update(PublicService.get_public_service(self._client, self.device_uuid, self.uuid))
