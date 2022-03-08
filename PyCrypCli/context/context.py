from __future__ import annotations

from typing import Callable, TYPE_CHECKING, TypeVar

import readline
from pypresence import PyPresenceException

from ..client import Client

if TYPE_CHECKING:
    from .root_context import RootContext
    from ..commands import Command


class Context:
    def __init__(self, root_context: RootContext):
        self.root_context: RootContext = root_context

        self.override_completions: list[str] | None = None
        self.history: list[str] = []

    def add_to_history(self, command: str) -> None:
        if self.history[-1:] != [command]:
            self.history.append(command)

    @property
    def prompt(self) -> str:
        return "$ "

    @property
    def client(self) -> Client:
        return self.root_context.client

    def get_commands(self) -> dict[str, Command]:
        return self.root_context.get_commands()

    def ask(self, prompt: str, options: list[str]) -> str:
        while True:
            try:
                choice: str = self.input_no_history(prompt, options).strip()
            except (KeyboardInterrupt, EOFError):
                print("\nEnter one of the following:", ", ".join(options))
                continue

            if choice in options:
                return choice

            print(f"'{choice}' is not one of the following:", ", ".join(options))

    def confirm(self, question: str) -> bool:
        return self.ask(question + " [yes|no] ", ["yes", "no"]) == "yes"

    def update_presence(
        self,
        state: str | None = None,
        details: str | None = None,
        start: int | None = None,
        end: int | None = None,
        large_image: str | None = None,
        large_text: str | None = None,
    ) -> None:
        if self.root_context.presence is None:
            return

        try:
            self.root_context.presence.update(
                state=state, details=details, start=start, end=end, large_image=large_image, large_text=large_text
            )
        except PyPresenceException:
            pass

    def enter_context(self) -> None:
        readline.clear_history()

    def leave_context(self) -> None:
        pass

    def reenter_context(self) -> None:
        self.restore_history()

    def input_no_history(self, prompt: str, override_completions: list[str] | None = None) -> str:
        readline.clear_history()
        old_override = self.override_completions
        self.override_completions = override_completions or []
        try:
            return input(prompt)
        finally:
            self.restore_history()
            self.override_completions = old_override

    def restore_history(self) -> None:
        readline.clear_history()
        for command in self.history:
            readline.add_history(command)

    def open(self, context: Context) -> None:
        self.root_context.open(context)

    def close(self) -> None:
        self.root_context.close()

    def loop_tick(self) -> None:
        pass

    def before_command(self) -> bool:
        return True


ContextType = TypeVar("ContextType", bound=Context)
COMMAND_FUNCTION = Callable[[ContextType, list[str]], None]
COMPLETER_FUNCTION = Callable[[ContextType, list[str]], list[str]]
