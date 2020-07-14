from datetime import datetime

from PyCrypCli.game_objects.game_object import GameObject
from PyCrypCli.util import convert_timestamp


class Transaction(GameObject):
    @property
    def timestamp(self) -> datetime:
        return convert_timestamp(datetime.fromisoformat(self._data.get("time_stamp")))

    @property
    def source_uuid(self) -> str:
        return self._data.get("source_uuid")

    @property
    def destination_uuid(self) -> str:
        return self._data.get("destination_uuid")

    @property
    def amount(self) -> int:
        return self._data.get("send_amount")

    @property
    def usage(self) -> str:
        return self._data.get("usage")

    @property
    def origin(self) -> int:
        return self._data.get("origin")
