from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .network_invitation import NetworkInvitation
from .network_membership import NetworkMembership
from ..model import Model

if TYPE_CHECKING:
    from ..device import Device
    from ...client import Client


class Network(Model):
    uuid: str
    hidden: bool
    owner_uuid: str = Field(alias="owner")
    name: str

    @staticmethod
    def get_public_networks(client: Client) -> list[Network]:
        return [Network.parse(client, net) for net in client.ms("network", ["public"])["networks"]]

    @staticmethod
    def get_by_uuid(client: Client, uuid: str) -> Network:
        return Network.parse(client, client.ms("network", ["get"], uuid=uuid))

    @staticmethod
    def get_network_by_name(client: Client, name: str) -> Network:
        return Network.parse(client, client.ms("network", ["name"], name=name))

    def get_members(self) -> list[NetworkMembership]:
        return [
            NetworkMembership.parse(self._client, member)
            for member in self._ms("network", ["members"], uuid=self.uuid)["members"]
        ]

    def request_membership(self, device: Device) -> NetworkInvitation:
        return NetworkInvitation.parse(
            self._client, self._ms("network", ["request"], uuid=self.uuid, device=device.uuid)
        )

    def get_membership_requests(self) -> list[NetworkInvitation]:
        return [
            NetworkInvitation.parse(self._client, invitation)
            for invitation in self._ms("network", ["requests"], uuid=self.uuid)["requests"]
        ]

    def invite_device(self, device: Device) -> NetworkInvitation:
        return NetworkInvitation.parse(
            self._client, self._ms("network", ["invite"], uuid=self.uuid, device=device.uuid)
        )

    def leave(self, device: Device) -> None:
        self._ms("network", ["leave"], uuid=self.uuid, device=device.uuid)

    def kick(self, device: Device) -> None:
        self._ms("network", ["kick"], uuid=self.uuid, device=device.uuid)

    def delete(self) -> None:
        self._ms("network", ["delete"], uuid=self.uuid)
