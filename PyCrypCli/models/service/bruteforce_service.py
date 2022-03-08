from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from pydantic import Field

from .service import Service
from ...exceptions import AttackNotRunningError

if TYPE_CHECKING:
    from ...client import Client


class BruteforceService(Service):
    target_device_uuid: str | None = Field(alias="target_device")
    target_service_uuid: str | None = Field(alias="target_service")
    started: datetime | None
    progress: float | None

    @staticmethod
    def get_bruteforce_service(client: Client, device_uuid: str) -> BruteforceService:
        service: Service = Service.get_service_by_name(client, device_uuid, "bruteforce")
        return BruteforceService.parse(
            client,
            service.dict(by_alias=True) | BruteforceService.get_bruteforce_details(client, device_uuid, service.uuid),
        )

    @staticmethod
    def get_bruteforce_details(client: Client, device_uuid: str, service_uuid: str) -> dict[Any, Any]:
        try:
            return client.ms("service", ["bruteforce", "status"], device_uuid=device_uuid, service_uuid=service_uuid)
        except AttackNotRunningError:
            return {"target_device_uuid": None, "target_service_uuid": None, "started": None, "progress": None}

    def update(self) -> BruteforceService:
        return self._update(BruteforceService.get_bruteforce_service(self._client, self.device_uuid))

    def attack(self, target_device: str, target_service: str) -> None:
        self._ms(
            "service",
            ["bruteforce", "attack"],
            device_uuid=self.device_uuid,
            service_uuid=self.uuid,
            target_device=target_device,
            target_service=target_service,
        )

    def stop(self) -> tuple[bool, float, str]:
        result = self._ms("service", ["bruteforce", "stop"], device_uuid=self.device_uuid, service_uuid=self.uuid)
        self.update()
        return result["access"], result["progress"], result["target_device"]
