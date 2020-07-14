from typing import Optional, List, Callable, Dict, TYPE_CHECKING

import readline
from pypresence import PyPresenceException

from PyCrypCli.client import Client

if TYPE_CHECKING:
    from PyCrypCli.commands import Command
    from PyCrypCli.context import RootContext


class Context:
    def __init__(self, root_context: "RootContext"):
        self.root_context: "RootContext" = root_context

        self.override_completions: Optional[List[str]] = None
        self.history: List[str] = []

    def add_to_history(self, command: str):
        if self.history[-1:] != [command]:
            self.history.append(command)

    @property
    def prompt(self) -> str:
        return "$ "

    @property
    def client(self) -> Client:
        return self.root_context.client

    def get_commands(self) -> Dict[str, "Command"]:
        return self.root_context.get_commands()

    def ask(self, prompt: str, options: List[str]) -> str:
        while True:
            try:
                choice: str = self.input_no_history(prompt, options).strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEnter one of the following:", ", ".join(options))
                continue
            if choice in options:
                return choice
            print(f"'{choice}' is not one of the following:", ", ".join(options))

    def update_presence(
        self,
        state: str = None,
        details: str = None,
        start: int = None,
        end: int = None,
        large_image: str = None,
        large_text: str = None,
    ):
        if self.root_context.presence is None:
            return
        try:
            self.root_context.presence.update(
                state=state, details=details, start=start, end=end, large_image=large_image, large_text=large_text
            )
        except PyPresenceException:
            pass

    def enter_context(self):
        readline.clear_history()

    def leave_context(self):
        pass

    def reenter_context(self):
        self.restore_history()

    def input_no_history(self, prompt: str, override_completions: Optional[List[str]] = None) -> Optional[str]:
        readline.clear_history()
        old_override: List[str] = self.override_completions
        self.override_completions: List[str] = override_completions or []
        try:
            return input(prompt)
        finally:
            self.restore_history()
            self.override_completions = old_override

    def restore_history(self):
        readline.clear_history()
        for command in self.history:
            readline.add_history(command)

    def open(self, context: "Context"):
        self.root_context.open(context)

    def close(self):
        self.root_context.close()

    def loop_tick(self):
        pass

    def before_command(self) -> bool:
        return True


COMMAND_FUNCTION = Callable[[Context, List[str]], None]
COMPLETER_FUNCTION = Callable[[Context, List[str]], List[str]]
