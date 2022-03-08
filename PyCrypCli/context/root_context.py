from __future__ import annotations

import re
from pathlib import Path
from typing import Type, TYPE_CHECKING

from pypresence import Presence, PyPresenceException

from .context import Context
from ..client import Client
from ..exceptions import InvalidServerURLError
from ..models import Config

if TYPE_CHECKING:
    from ..commands import Command


class RootContext:
    def __init__(self, server: str, config_file: Path, commands: dict[Type[Context], dict[str, Command]]):
        self.client: Client = Client(server)

        if not (match := re.match(r"^wss?://(.+)$", server)):
            raise InvalidServerURLError

        self.host: str = match.group(1).split("/")[0]

        self.config_file: Path = config_file

        self.context_stack: list[Context] = []

        self.commands: dict[Type[Context], dict[str, Command]] = commands

        try:
            self.presence: Presence = Presence(client_id="596676243144048640")
            self.presence.connect()
        except (PyPresenceException, FileNotFoundError, ConnectionRefusedError):
            self.presence = None

    def open(self, context: Context) -> None:
        self.context_stack.append(context)
        context.enter_context()

    def close(self) -> None:
        self.context_stack.pop().leave_context()
        self.get_context().reenter_context()

    def get_context(self) -> "Context":
        return self.context_stack[-1]

    def get_override_completions(self) -> list[str] | None:
        return self.get_context().override_completions

    def get_commands(self) -> dict[str, Command]:
        return self.commands[type(self.get_context())]

    def read_config_file(self) -> Config:
        if not self.config_file.exists():
            self.write_config_file(Config.get_default_config())

        return Config.parse_raw(self.config_file.read_text())

    def write_config_file(self, config: Config) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(config.json())
