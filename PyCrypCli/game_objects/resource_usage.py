from PyCrypCli.game_objects.game_object import GameObject


class ResourceUsage(GameObject):
    @property
    def cpu(self) -> float:
        return min(1, self._data["usage_cpu"] / self._data["performance_cpu"])

    @property
    def ram(self) -> float:
        return min(1, self._data["usage_ram"] / self._data["performance_ram"])

    @property
    def gpu(self) -> float:
        return min(1, self._data["usage_gpu"] / self._data["performance_gpu"])

    @property
    def disk(self) -> float:
        return min(1, self._data["usage_disk"] / self._data["performance_disk"])

    @property
    def network(self) -> float:
        return min(1, self._data["usage_network"] / self._data["performance_network"])
