from PyCrypCli.game_objects.game_object import GameObject


class NetworkMembership(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def network(self) -> str:
        return self._data.get("network")

    @property
    def device(self) -> str:
        return self._data.get("device")
