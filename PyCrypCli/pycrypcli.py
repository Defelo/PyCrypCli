import os
import sys
from os import getenv
from typing import List, Optional

import requests
import sentry_sdk

from PyCrypCli.commands import make_commands, Command
from PyCrypCli.context import Context, LoginContext, RootContext

try:
    import readline
except ImportError:
    import pyreadline as readline

if not getenv("DEBUG"):
    response = requests.get("https://sentrydsn.defelo.ml/pycrypcli")
    if response.ok:
        sentry_sdk.init(dsn=response.text, attach_stacktrace=True, shutdown_timeout=5)


class Frontend:
    def __init__(self, server: str, config_file: List[str]):
        self.config_file: List[str] = config_file

        self.history: List[str] = []

        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.completer)
        readline.set_completer_delims(" ")

        self.root_context: RootContext = RootContext(server, config_file, make_commands())
        self.root_context.open(LoginContext(self.root_context))

    def complete_command(self, text: str) -> List[str]:
        override_completions: Optional[List[str]] = self.root_context.get_override_completions()
        if override_completions is not None:
            return override_completions

        cmd, *args = text.split(" ") or [""]
        if not args:
            return list(self.root_context.get_commands())

        comp: Optional[Command] = self.root_context.get_commands().get(cmd, None)
        if comp is None:
            return []

        return comp.handle_completer(self.get_context(), args) or []

    def completer(self, text: str, state: int) -> Optional[str]:
        readline.set_completer_delims(" ")
        options: List[str] = self.complete_command(readline.get_line_buffer())
        options: List[str] = [o + " " if o[-1:] != "\0" else o[:-1] for o in sorted(options) if o.startswith(text)]

        if state < len(options):
            return options[state]
        return None

    def get_context(self) -> Context:
        return self.root_context.get_context()

    def mainloop(self):
        while True:
            self.get_context().loop_tick()
            context: Context = self.get_context()

            try:
                cmd, *args = input(context.prompt).strip().split(" ")
                if not cmd:
                    continue
            except EOFError:  # Ctrl-D
                print("exit")
                cmd, args = "exit", []
            except KeyboardInterrupt:  # Ctrl-C
                print("^C")
                continue

            if not context.before_command():
                continue

            context.add_to_history(cmd + " " + " ".join(args))

            if cmd in context.get_commands():
                context.get_commands()[cmd].handle(context, args)
            else:
                print("Command could not be found.")
                print("Type `help` for a list of commands.")


def main():
    print(
        "\033[32m\033[1m"
        r"""
       ______                 __  _
      / ____/______  ______  / /_(_)____
     / /   / ___/ / / / __ \/ __/ / ___/
    / /___/ /  / /_/ / /_/ / /_/ / /__
    \____/_/   \__, / .___/\__/_/\___/
              /____/_/
"""
        "\033[0m"
    )
    print("Python Cryptic Game Client (https://github.com/Defelo/PyCrypCli)")
    print("You can always type `help` for a list of available commands.")

    server: str = "wss://ws.cryptic-game.net/"
    if len(sys.argv) > 1:
        server: str = sys.argv[1]
        if server.lower() == "test":
            server: str = "wss://ws.test.cryptic-game.net/"
        elif not server.startswith("wss://") and not server.startswith("ws://"):
            server: str = "ws://" + server

    frontend: Frontend = Frontend(server, [os.path.expanduser("~"), ".config", "PyCrypCli", "config.json"])
    frontend.mainloop()


if __name__ == "__main__":
    main()
