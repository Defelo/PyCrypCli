from PyCrypCli.game_objects.game_object import GameObject


class NetworkInvitation(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def network(self) -> str:
        return self._data.get("network")

    @property
    def device(self) -> str:
        return self._data.get("device")

    @property
    def request(self) -> bool:
        return self._data.get("request")

    def accept(self):
        self._ms("network", ["accept"], uuid=self.uuid)

    def deny(self):
        self._ms("network", ["deny"], uuid=self.uuid)
