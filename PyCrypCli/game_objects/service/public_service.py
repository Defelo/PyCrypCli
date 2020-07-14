from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject


class PublicService(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def device(self) -> str:
        return self._data.get("device")

    @property
    def name(self) -> str:
        return self._data.get("name")

    @property
    def running_port(self) -> int:
        return self._data.get("running_port")

    @staticmethod
    def get_public_service(client: Client, device_uuid: str, service_uuid: str) -> "PublicService":
        return PublicService(
            client, client.ms("service", ["public_info"], device_uuid=device_uuid, service_uuid=service_uuid)
        )

    def update(self):
        self._update(PublicService.get_public_service(self._client, self.device, self.uuid))
