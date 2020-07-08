from typing import List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.service.public_service import PublicService
from PyCrypCli.game_objects.service.service import Service


class PortscanService(Service):
    @staticmethod
    def get_portscan_service(client: Client, device_uuid: str) -> "PortscanService":
        service: Service = Service.get_service_by_name(client, device_uuid, "portscan")
        return PortscanService(client, service._data)

    def update(self):
        self._update(PortscanService.get_portscan_service(self._client, self.device))

    def use(self, target: str) -> List[PublicService]:
        return [PublicService(self._client, service) for service in super().use(target_device=target)["services"]]
