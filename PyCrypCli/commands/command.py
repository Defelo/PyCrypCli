from __future__ import annotations

from importlib import import_module
from typing import Callable, Type

from ..context import Context, COMMAND_FUNCTION, COMPLETER_FUNCTION, ContextType
from ..exceptions import CommandRegistrationError, NoDocStringError


class CommandError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg: str = msg


class Command:
    def __init__(
        self,
        name: str,
        func: COMMAND_FUNCTION[ContextType],
        description: str,
        contexts: list[Type[Context]],
        aliases: list[str],
    ):
        self.name: str = name
        self.func: COMMAND_FUNCTION[ContextType] = func
        self.description: str = description
        self.contexts: list[Type[Context]] = contexts
        self.aliases: list[str] = aliases
        self.completer_func: COMPLETER_FUNCTION[ContextType] | None = None
        self.subcommands: list[Command] = []
        self.prepared_subcommands: dict[Type[Context], dict[str, Command]] = {}

    def __call__(self, context: ContextType, args: list[str]) -> None:
        self.func(context, args)

    def parse_command(self, context: Context, args: list[str]) -> tuple[Command, list[str]]:
        prepared_subcommands = self.prepared_subcommands.get(type(context), {})
        if args:
            cmd: Command | None = prepared_subcommands.get(args[0])
            if cmd is not None:
                return cmd.parse_command(context, args[1:])

        return self, args

    def handle(self, context: ContextType, args: list[str]) -> None:
        cmd, args = self.parse_command(context, args)
        try:
            cmd.func(context, args)
        except CommandError as error:
            print(error.msg)

    def handle_completer(self, context: ContextType, args: list[str]) -> list[str]:
        cmd, args = self.parse_command(context, args)

        out = list(cmd.prepared_subcommands.get(type(context), {}))
        if cmd.completer_func is not None:
            out += cmd.completer_func(context, args) or []

        return out

    def completer(self) -> Callable[[COMPLETER_FUNCTION[ContextType]], COMPLETER_FUNCTION[ContextType]]:
        def decorator(func: COMPLETER_FUNCTION[ContextType]) -> COMPLETER_FUNCTION[ContextType]:
            self.completer_func = func
            return func

        return decorator

    def subcommand(
        self, name: str, *, contexts: list[Type[Context]] | None = None, aliases: list[str] | None = None
    ) -> Callable[[COMMAND_FUNCTION[ContextType]], "Command"]:
        def decorator(func: COMMAND_FUNCTION[ContextType]) -> Command:
            if func.__doc__ is None:
                raise NoDocStringError(name, subcommand=True)
            desc: str = func.__doc__
            desc = "\n".join(map(str.strip, desc.splitlines())).strip()
            cmd = Command(name, func, desc, contexts or self.contexts, aliases or [])
            self.subcommands.append(cmd)
            return cmd

        return decorator

    def make_subcommands(self) -> None:
        for cmd in self.subcommands:
            for context in cmd.contexts:
                for name in [cmd.name] + cmd.aliases:
                    if name in self.prepared_subcommands.setdefault(context, {}):
                        raise CommandRegistrationError(name, subcommand=True)
                    self.prepared_subcommands[context][name] = cmd
            cmd.make_subcommands()


commands: list[Command] = []


def command(
    name: str, contexts: list[Type[Context]], aliases: list[str] | None = None
) -> Callable[[COMMAND_FUNCTION[ContextType]], Command]:
    def decorator(func: COMMAND_FUNCTION[ContextType]) -> Command:
        if func.__doc__ is None:
            raise NoDocStringError(name)
        desc: str = func.__doc__
        desc = "\n".join(map(str.strip, desc.splitlines())).strip()
        cmd = Command(name, func, desc, contexts, aliases or [])
        commands.append(cmd)
        return cmd

    return decorator


def make_commands() -> dict[Type[Context], dict[str, Command]]:
    for module in [
        "account",
        "help",
        "shell",
        "status",
        "device",
        "files",
        "morphcoin",
        "service",
        "miner",
        "inventory",
        "shop",
        "network",
    ]:
        import_module(f"PyCrypCli.commands.{module}")

    result: dict[Type[Context], dict[str, Command]] = {}
    for cmd in commands:
        for context in cmd.contexts:
            for name in [cmd.name] + cmd.aliases:
                if name in result.setdefault(context, {}):
                    raise CommandRegistrationError(name)
                result[context][name] = cmd
        cmd.make_subcommands()
    return result
