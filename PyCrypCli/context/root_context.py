import json
import os
import re
from typing import List, Dict, Type, Tuple, Optional

from pypresence import Presence, InvalidPipe

from PyCrypCli.client import Client
from PyCrypCli.context.context import Context, COMMAND_FUNCTION, COMPLETER_FUNCTION


class RootContext:
    def __init__(
        self,
        server: str,
        config_file: List[str],
        commands: Dict[Type[Context], Dict[str, Tuple[str, COMMAND_FUNCTION, COMPLETER_FUNCTION]]],
    ):
        self.client: Client = Client(server)
        self.host: str = re.match(r"^wss?://(.+)$", server).group(1).split("/")[0]

        self.config_file: List[str] = config_file

        self.context_stack: List[Context] = []

        self.commands: Dict[Type[Context], Dict[str, Tuple[str, COMMAND_FUNCTION, COMPLETER_FUNCTION]]] = commands

        self.presence: Presence = Presence(client_id="596676243144048640")
        try:
            self.presence.connect()
        except (FileNotFoundError, InvalidPipe):
            self.presence = None

    def open(self, context: "Context"):
        self.context_stack.append(context)
        context.enter_context()

    def close(self):
        self.context_stack.pop().leave_context()
        self.get_context().reenter_context()

    def get_context(self) -> "Context":
        return self.context_stack[-1]

    def get_override_completions(self) -> Optional[List[str]]:
        return self.get_context().override_completions

    def get_commands(self) -> Dict[str, Tuple[str, "COMMAND_FUNCTION", "COMPLETER_FUNCTION"]]:
        return self.commands[type(self.get_context())]

    def read_config_file(self) -> dict:
        for i in range(1, len(self.config_file)):
            path: str = os.path.join(*self.config_file[:i])
            if not os.path.exists(path):
                os.mkdir(path)
        path: str = os.path.join(*self.config_file)
        if not os.path.exists(path):
            self.write_config_file({"servers": {}})
        return json.load(open(path))

    def write_config_file(self, config: dict):
        path: str = os.path.join(*self.config_file)
        with open(path, "w") as file:
            json.dump(config, file)
            file.flush()
