from typing import Callable, List, Dict, Type, Optional

from PyCrypCli.context import Context, COMMAND_FUNCTION, COMPLETER_FUNCTION


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

    def __call__(self, context: Context, args: List[str]):
        return self.func(context, args)

    def completer(self):
        def decorator(func: COMPLETER_FUNCTION) -> COMPLETER_FUNCTION:
            self.completer_func = func
            return func

        return decorator


commands: List[Command] = []


def command(
    name: str, contexts: List[Type[Context]], desc: str, aliases: List[str] = None
) -> Callable[[COMMAND_FUNCTION], Command]:
    def decorator(func: COMMAND_FUNCTION) -> Command:
        cmd = Command(name, func, desc, contexts, aliases or [])
        commands.append(cmd)
        return cmd

    return decorator


def make_commands() -> Dict[Type[Context], Dict[str, Command]]:
    # noinspection PyUnresolvedReferences
    from PyCrypCli.commands import status, device, files, morphcoin, service, miner, inventory, shop, network

    result: Dict[Type[Context], Dict[str, Command]] = {}
    for cmd in commands:
        for context in cmd.contexts:
            for name in [cmd.name] + cmd.aliases:
                assert name not in result.setdefault(context, {})
                result[context][name] = cmd
    return result
