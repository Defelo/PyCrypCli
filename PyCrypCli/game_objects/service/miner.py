from datetime import datetime
from typing import Optional, List

from PyCrypCli.client import Client, ServiceNotFoundException
from PyCrypCli.game_objects.service.service import Service
from PyCrypCli.util import convert_timestamp


class Miner(Service):
    @property
    def wallet(self) -> Optional[str]:
        return self._data.get("wallet")

    @property
    def started(self) -> Optional[datetime]:
        timestamp: Optional[str] = self._data.get("started")
        if timestamp is not None:
            return convert_timestamp(timestamp)

    @property
    def power(self) -> Optional[float]:
        return self._data.get("power")

    @staticmethod
    def get_miner(client: Client, device_uuid: str) -> "Miner":
        for service in Service.get_services(client, device_uuid):
            if service.name == "miner":
                miner = Miner(client, service._data)
                miner._update({**service._data, **miner.get_miner_details()})
                return miner
        raise ServiceNotFoundException

    @staticmethod
    def get_miners(client: Client, wallet_uuid: str) -> List["Miner"]:
        return [
            Miner(client, {**miner["service"], **miner["miner"]})
            for miner in client.ms("service", ["miner", "list"], wallet_uuid=wallet_uuid)["miners"]
        ]

    def get_miner_details(self) -> dict:
        return self._ms("service", ["miner", "get"], service_uuid=self.uuid)

    def update(self):
        self._update(Miner.get_miner(self._client, self.device))

    def set_power(self, power: float):
        self._update(self._ms("service", ["miner", "power"], service_uuid=self.uuid, power=power))

    def set_wallet(self, wallet_uuid: str):
        self._update(self._ms("service", ["miner", "wallet"], service_uuid=self.uuid, wallet_uuid=wallet_uuid))
