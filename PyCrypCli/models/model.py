from __future__ import annotations

from typing import Type, TypeVar, Any, TYPE_CHECKING

from pydantic import BaseModel, PrivateAttr, ValidationError

if TYPE_CHECKING:
    from ..client import Client

ModelType = TypeVar("ModelType", bound="Model")


class Model(BaseModel):
    _client: Client = PrivateAttr()

    @classmethod
    def parse(cls: Type[ModelType], client: Client, obj: dict[Any, Any]) -> ModelType:
        out = cls.parse_obj(obj)
        out._client = client
        return out

    def _ms(self, microservice: str, endpoint: list[str], **data: Any) -> dict[Any, Any]:
        return self._client.ms(microservice, endpoint, **data)

    def _update(self: ModelType, obj: ModelType | dict[Any, Any]) -> ModelType:
        if isinstance(obj, dict):
            obj = self.validate(obj)
        for k, v in obj.dict().items():
            setattr(self, k, v)
        return self
