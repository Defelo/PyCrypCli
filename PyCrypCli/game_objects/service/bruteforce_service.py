from datetime import datetime
from typing import Optional, Tuple

from PyCrypCli.client import Client
from PyCrypCli.exceptions import AttackNotRunningException
from PyCrypCli.game_objects.service.service import Service


class BruteforceService(Service):
    @property
    def target_device(self) -> Optional[str]:
        return self._data.get("target_device")

    @property
    def target_service(self) -> Optional[str]:
        return self._data.get("target_service")

    @property
    def started(self) -> Optional[datetime]:
        timestamp: Optional[int] = self._data.get("started")
        if timestamp is None:
            return None

        return datetime.fromtimestamp(timestamp)

    @property
    def progress(self) -> Optional[float]:
        return self._data.get("progress")

    @staticmethod
    def get_bruteforce_service(client: Client, device_uuid: str) -> "BruteforceService":
        service: BruteforceService = Service.get_service_by_name(client, device_uuid, "bruteforce").clone(
            BruteforceService
        )
        service._update(service.get_bruteforce_details())
        return service

    def get_bruteforce_details(self) -> dict:
        try:
            return self._ms("service", ["bruteforce", "status"], device_uuid=self.device, service_uuid=self.uuid)
        except AttackNotRunningException:
            return {}

    def update(self):
        self._update(BruteforceService.get_bruteforce_service(self._client, self.device))

    def attack(self, target_device: str, target_service: str):
        self._ms(
            "service",
            ["bruteforce", "attack"],
            device_uuid=self.device,
            service_uuid=self.uuid,
            target_device=target_device,
            target_service=target_service,
        )

    def stop(self) -> Tuple[bool, float, str]:
        result = self._ms("service", ["bruteforce", "stop"], device_uuid=self.device, service_uuid=self.uuid)
        self.update()
        return result["access"], result["progress"], result["target_device"]
