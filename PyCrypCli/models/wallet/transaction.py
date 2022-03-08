from datetime import datetime

from pydantic import Field, validator

from ..model import Model
from ...util import utc_to_local


class Transaction(Model):
    timestamp: datetime = Field(alias="time_stamp")
    source_uuid: str
    destination_uuid: str
    amount: int = Field(alias="send_amount")
    usage: str
    origin: str

    @validator("timestamp")
    def _convert_timestamp(cls, value: datetime) -> datetime:
        return utc_to_local(value)
