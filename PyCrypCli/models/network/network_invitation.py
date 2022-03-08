from pydantic import Field

from ..model import Model


class NetworkInvitation(Model):
    uuid: str
    network_uuid: str = Field(alias="network")
    device_uuid: str = Field(alias="device")
    request: bool

    def accept(self) -> None:
        self._ms("network", ["accept"], uuid=self.uuid)

    def deny(self) -> None:
        self._ms("network", ["deny"], uuid=self.uuid)
