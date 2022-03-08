from __future__ import annotations

from datetime import datetime
from typing import Any, TYPE_CHECKING

from pydantic import Field

from .service import Service

if TYPE_CHECKING:
    from ...client import Client


class Miner(Service):
    wallet_uuid: str = Field(alias="wallet")
    started: datetime | None
    power: float

    @staticmethod
    def get_miner(client: Client, device_uuid: str) -> Miner:
        service: Service = Service.get_service_by_name(client, device_uuid, "miner")
        return Miner.parse(client, service.dict(by_alias=True) | Miner.get_miner_details(client, service.uuid))

    @staticmethod
    def get_miners(client: Client, wallet_uuid: str) -> list[Miner]:
        return [
            Miner.parse(client, {**miner["service"], **miner["miner"]})
            for miner in client.ms("service", ["miner", "list"], wallet_uuid=wallet_uuid)["miners"]
        ]

    @staticmethod
    def get_miner_details(client: Client, service_uuid: str) -> dict[Any, Any]:
        return client.ms("service", ["miner", "get"], service_uuid=service_uuid)

    def update(self) -> Miner:
        return self._update(Miner.get_miner(self._client, self.device_uuid))

    def set_power(self, power: float) -> Miner:
        self._ms("service", ["miner", "power"], service_uuid=self.uuid, power=power)
        return self.update()

    def set_wallet(self, wallet_uuid: str) -> Miner:
        self._ms("service", ["miner", "wallet"], service_uuid=self.uuid, wallet_uuid=wallet_uuid)
        return self.update()
