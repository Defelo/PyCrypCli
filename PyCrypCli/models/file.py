from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .model import Model

if TYPE_CHECKING:
    from ..client import Client


class File(Model):
    uuid: str | None
    device_uuid: str = Field(alias="device")
    name: str = Field(alias="filename")
    content: str
    is_directory: bool
    parent_dir_uuid: str | None

    @property
    def is_root_directory(self) -> bool:
        return self.uuid is None

    @staticmethod
    def get_root_directory(client: Client, device_uuid: str) -> File:
        return File.parse(
            client,
            {
                "uuid": None,
                "device": device_uuid,
                "filename": "",
                "content": "",
                "is_directory": True,
                "parent_dir_uuid": None,
            },
        )

    @staticmethod
    def get_file(client: Client, device_uuid: str, file_uuid: str) -> File:
        return File.parse(client, client.ms("device", ["file", "info"], device_uuid=device_uuid, file_uuid=file_uuid))

    def update(self) -> File:
        if not self.uuid:
            return self

        return self._update(File.get_file(self._client, self.device_uuid, self.uuid))

    def move(self, new_filename: str, new_parent_dir_uuid: str | None) -> File:
        return self._update(
            self._ms(
                "device",
                ["file", "move"],
                device_uuid=self.device_uuid,
                file_uuid=self.uuid,
                new_filename=new_filename,
                new_parent_dir_uuid=new_parent_dir_uuid,
            )
        )

    def edit(self, new_content: str) -> File:
        return self._update(
            self._ms(
                "device", ["file", "update"], device_uuid=self.device_uuid, file_uuid=self.uuid, content=new_content
            )
        )

    def delete(self) -> None:
        self._ms("device", ["file", "delete"], device_uuid=self.device_uuid, file_uuid=self.uuid)
