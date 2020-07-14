from PyCrypCli.game_objects.game_object import GameObject


class ResourceUsage(GameObject):
    @property
    def cpu(self) -> float:
        return self._data.get("cpu")

    @property
    def ram(self) -> float:
        return self._data.get("ram")

    @property
    def gpu(self) -> float:
        return self._data.get("gpu")

    @property
    def disk(self) -> float:
        return self._data.get("disk")

    @property
    def network(self) -> float:
        return self._data.get("network")
