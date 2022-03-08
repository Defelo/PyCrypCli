from pydantic import Field

from ..model import Model


class NetworkMembership(Model):
    uuid: str
    network_uuid: str = Field(alias="network")
    device_uuid: str = Field(alias="device")
