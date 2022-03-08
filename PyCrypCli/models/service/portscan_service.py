from __future__ import annotations

from typing import TYPE_CHECKING

from .public_service import PublicService
from .service import Service

if TYPE_CHECKING:
    from ...client import Client


class PortscanService(Service):
    @staticmethod
    def get_portscan_service(client: Client, device_uuid: str) -> PortscanService:
        service: Service = Service.get_service_by_name(client, device_uuid, "portscan")
        return PortscanService.parse(client, service.dict(by_alias=True))

    def update(self) -> PortscanService:
        return self._update(PortscanService.get_portscan_service(self._client, self.device_uuid))

    def scan(self, target: str) -> list[PublicService]:
        return [PublicService.parse(self._client, service) for service in self.use(target_device=target)["services"]]
