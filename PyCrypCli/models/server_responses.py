from datetime import datetime

from pydantic import Field

from .model import Model


class StatusResponse(Model):
    online: int


class InfoResponse(Model):
    name: str
    uuid: str
    created: datetime
    last_login: datetime = Field(alias="last")
    online: int


class TokenResponse(Model):
    token: str
