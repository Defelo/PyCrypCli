from importlib import import_module
from typing import Callable, List, Dict, Type, Optional, Tuple

from PyCrypCli.context import Context, COMMAND_FUNCTION, COMPLETER_FUNCTION
from PyCrypCli.exceptions import CommandRegistrationException, NoDocStringException


class CommandError(Exception):
    def __init__(self, msg: str):
        super().__init__()
        self.msg: str = msg


class Command:
    def __init__(
        self, name: str, func: COMMAND_FUNCTION, description: str, contexts: List[Type[Context]], aliases: List[str]
    ):
        self.name: str = name
        self.func: COMMAND_FUNCTION = func
        self.description: str = description
        self.contexts: List[Type[Context]] = contexts
        self.aliases: List[str] = aliases
        self.completer_func: Optional[COMPLETER_FUNCTION] = None
        self.subcommands: List[Command] = []
        self.prepared_subcommands: Dict[Type[Context], Dict[str, Command]] = {}

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def parse_command(self, context: Context, args: List[str]) -> Tuple["Command", List[str]]:
        prepared_subcommands = self.prepared_subcommands.get(type(context), {})
        if args:
            cmd: Optional[Command] = prepared_subcommands.get(args[0])
            if cmd is not None:
                return cmd.parse_command(context, args[1:])

        return self, args

    def handle(self, context: Context, args: List[str]):
        cmd, args = self.parse_command(context, args)
        try:
            cmd.func(context, args)
        except CommandError as error:
            print(error.msg)

    def handle_completer(self, context: Context, args: List[str]) -> List[str]:
        cmd, args = self.parse_command(context, args)

        out = list(cmd.prepared_subcommands.get(type(context), {}))
        if cmd.completer_func is not None:
            out += cmd.completer_func(context, args) or []

        return out

    def completer(self):
        def decorator(func: COMPLETER_FUNCTION) -> COMPLETER_FUNCTION:
            self.completer_func = func
            return func

        return decorator

    def subcommand(
        self, name: str, *, contexts: List[Type[Context]] = None, aliases: List[str] = None
    ) -> Callable[[COMMAND_FUNCTION], "Command"]:
        if contexts is None:
            contexts = self.contexts

        def decorator(func: COMMAND_FUNCTION) -> Command:
            if func.__doc__ is None:
                raise NoDocStringException(name, subcommand=True)
            desc: str = func.__doc__
            desc = "\n".join(map(str.strip, desc.splitlines())).strip()
            cmd = Command(name, func, desc, contexts, aliases or [])
            self.subcommands.append(cmd)
            return cmd

        return decorator

    def make_subcommands(self):
        for cmd in self.subcommands:
            for context in cmd.contexts:
                for name in [cmd.name] + cmd.aliases:
                    if name in self.prepared_subcommands.setdefault(context, {}):
                        raise CommandRegistrationException(name, subcommand=True)
                    self.prepared_subcommands[context][name] = cmd
            cmd.make_subcommands()


commands: List[Command] = []


def command(
    name: str, contexts: List[Type[Context]], aliases: List[str] = None
) -> Callable[[COMMAND_FUNCTION], Command]:
    def decorator(func: COMMAND_FUNCTION) -> Command:
        if func.__doc__ is None:
            raise NoDocStringException(name)
        desc: str = func.__doc__
        desc = "\n".join(map(str.strip, desc.splitlines())).strip()
        cmd = Command(name, func, desc, contexts, aliases or [])
        commands.append(cmd)
        return cmd

    return decorator


def make_commands() -> Dict[Type[Context], Dict[str, Command]]:
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

    result: Dict[Type[Context], Dict[str, Command]] = {}
    for cmd in commands:
        for context in cmd.contexts:
            for name in [cmd.name] + cmd.aliases:
                if name in result.setdefault(context, {}):
                    raise CommandRegistrationException(name)
                result[context][name] = cmd
        cmd.make_subcommands()
    return result
