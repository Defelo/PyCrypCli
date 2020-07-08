from typing import List, Union, Type, TypeVar

from PyCrypCli.client import Client

T = TypeVar("T")


class GameObject:
    def __init__(self, client: Client, data: dict):
        self._client: Client = client
        self._data: dict = data

    def __repr__(self):
        out: str = self.__class__.__name__ + "("
        members = []
        for key in dir(self):
            if key.startswith("_"):
                continue
            value = getattr(self, key)
            if not callable(value):
                members.append(f"{key}={repr(value)}")
        out += ", ".join(members)
        out += ")"
        return out

    def _ms(self, microservice: str, endpoint: List[str], **data) -> dict:
        return self._client.ms(microservice, endpoint, **data)

    def _update(self, data: Union["GameObject", dict]):
        self._data.update(data if isinstance(data, dict) else data._data)

    def update(self):
        pass

    def clone(self, cls: Type[T]) -> T:
        return cls(self._client, self._data)
