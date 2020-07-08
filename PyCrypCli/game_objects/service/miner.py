from datetime import datetime
from typing import Optional, List

from PyCrypCli.client import Client
from PyCrypCli.game_objects.service.service import Service


class Miner(Service):
    @property
    def wallet(self) -> Optional[str]:
        return self._data.get("wallet")

    @property
    def started(self) -> Optional[datetime]:
        timestamp: Optional[int] = self._data.get("started")
        if timestamp is None:
            return None

        return datetime.fromtimestamp(timestamp / 1000)

    @property
    def power(self) -> Optional[float]:
        return self._data.get("power")

    @staticmethod
    def get_miner(client: Client, device_uuid: str) -> "Miner":
        miner: Miner = Service.get_service_by_name(client, device_uuid, "miner").clone(Miner)
        miner._update(miner.get_miner_details())
        return miner

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
        self._ms("service", ["miner", "power"], service_uuid=self.uuid, power=power)
        self.update()

    def set_wallet(self, wallet_uuid: str):
        self._ms("service", ["miner", "wallet"], service_uuid=self.uuid, wallet_uuid=wallet_uuid)
        self.update()
