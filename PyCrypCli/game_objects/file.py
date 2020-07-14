from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject


class File(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def device(self) -> str:
        return self._data.get("device")

    @property
    def filename(self) -> str:
        return self._data.get("filename")

    @property
    def content(self) -> str:
        return self._data.get("content")

    @property
    def is_directory(self) -> bool:
        return self._data.get("is_directory")

    @property
    def parent_dir_uuid(self) -> str:
        return self._data.get("parent_dir_uuid")

    @staticmethod
    def get_file(client: Client, device_uuid: str, file_uuid: str) -> "File":
        return File(client, client.ms("device", ["file", "info"], device_uuid=device_uuid, file_uuid=file_uuid))

    def update(self):
        self._update(File.get_file(self._client, self.device, self.uuid))

    def move(self, new_filename: str, new_parent_dir_uuid: str):
        self._update(
            self._ms(
                "device",
                ["file", "move"],
                device_uuid=self.device,
                file_uuid=self.uuid,
                new_filename=new_filename,
                new_parent_dir_uuid=new_parent_dir_uuid,
            )
        )

    def edit(self, new_content: str):
        self._update(
            self._ms("device", ["file", "update"], device_uuid=self.device, file_uuid=self.uuid, content=new_content,)
        )

    def delete(self):
        self._ms("device", ["file", "delete"], device_uuid=self.device, file_uuid=self.uuid)
