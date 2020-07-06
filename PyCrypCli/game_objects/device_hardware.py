from PyCrypCli.game_objects.game_object import GameObject


class DeviceHardware(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def device(self) -> str:
        return self._data.get("device_uuid")

    @property
    def hardware_element(self) -> str:
        return self._data.get("hardware_element")

    @property
    def hardware_type(self) -> str:
        return self._data.get("hardware_type")
