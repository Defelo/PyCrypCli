from __future__ import annotations

from pydantic import BaseModel


class ServerConfig(BaseModel):
    token: str | None


class Config(BaseModel):
    servers: dict[str, ServerConfig]

    @staticmethod
    def get_default_config() -> Config:
        return Config(servers={})
