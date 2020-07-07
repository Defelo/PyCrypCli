from typing import List, TYPE_CHECKING

from PyCrypCli.client import Client
from PyCrypCli.game_objects.game_object import GameObject
from PyCrypCli.game_objects.network.network_invitation import NetworkInvitation
from PyCrypCli.game_objects.network.network_membership import NetworkMembership

if TYPE_CHECKING:
    from PyCrypCli.game_objects.device import Device


class Network(GameObject):
    @property
    def uuid(self) -> str:
        return self._data.get("uuid")

    @property
    def hidden(self) -> bool:
        return self._data.get("hidden")

    @property
    def owner(self) -> str:
        return self._data.get("owner")

    @property
    def name(self) -> str:
        return self._data.get("name")

    @staticmethod
    def get_public_networks(client: Client) -> List["Network"]:
        return [Network(client, net) for net in client.ms("network", ["public"])["networks"]]

    @staticmethod
    def get_by_uuid(client: Client, uuid: str) -> "Network":
        return Network(client, client.ms("network", ["get"], uuid=uuid))

    @staticmethod
    def get_network_by_name(client: Client, name: str) -> "Network":
        return Network(client, client.ms("network", ["name"], name=name))

    def get_members(self) -> List[NetworkMembership]:
        return [
            NetworkMembership(self._client, member)
            for member in self._ms("network", ["members"], uuid=self.uuid)["members"]
        ]

    def request_membership(self, device: "Device") -> NetworkInvitation:
        return NetworkInvitation(self._client, self._ms("network", ["request"], uuid=self.uuid, device=device.uuid))

    def get_membership_requests(self) -> List[NetworkInvitation]:
        return [
            NetworkInvitation(self._client, invitation)
            for invitation in self._ms("network", ["requests"], uuid=self.uuid)["requests"]
        ]

    def invite_device(self, device: "Device") -> NetworkInvitation:
        return NetworkInvitation(self._client, self._ms("network", ["invite"], uuid=self.uuid, device=device.uuid))

    def leave(self, device: "Device"):
        self._ms("network", ["leave"], uuid=self.uuid, device=device.uuid)

    def kick(self, device: "Device"):
        self._ms("network", ["kick"], uuid=self.uuid, device=device.uuid)

    def delete(self):
        self._ms("network", ["delete"], uuid=self.uuid)
