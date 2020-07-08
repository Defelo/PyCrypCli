from typing import List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.service.public_service import PublicService
from PyCrypCli.game_objects.service.service import Service


class PortscanService(Service):
    @staticmethod
    def get_portscan_service(client: Client, device_uuid: str) -> "PortscanService":
        return Service.get_service_by_name(client, device_uuid, "portscan").clone(PortscanService)

    def update(self):
        self._update(PortscanService.get_portscan_service(self._client, self.device))

    def scan(self, target: str) -> List[PublicService]:
        return [PublicService(self._client, service) for service in self.use(target_device=target)["services"]]
