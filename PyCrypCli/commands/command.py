from typing import Callable, List, Tuple, Dict, Type

from PyCrypCli.context import Context, COMMAND_FUNCTION, COMPLETER_FUNCTION

commands: List[Tuple[List[str], List[Type[Context]], str, COMMAND_FUNCTION]] = []
completers: Dict[COMMAND_FUNCTION, COMPLETER_FUNCTION] = {}


def command(
    cmds: List[str], contexts: List[Type[Context]], desc: str
) -> Callable[[COMMAND_FUNCTION], COMMAND_FUNCTION]:
    def decorator(func: COMMAND_FUNCTION) -> COMMAND_FUNCTION:
        commands.append((cmds, contexts, desc, func))
        return func

    return decorator


def completer(cmds: List[COMMAND_FUNCTION]) -> Callable:
    def decorator(func: COMPLETER_FUNCTION) -> COMPLETER_FUNCTION:
        for cmd in cmds:
            assert cmd not in completers
            completers[cmd] = func
        return func

    return decorator


def make_commands() -> Dict[Type[Context], Dict[str, Tuple[str, COMMAND_FUNCTION, COMPLETER_FUNCTION]]]:
    # noinspection PyUnresolvedReferences
    from PyCrypCli.commands import status, device, files, morphcoin, service, miner, inventory, shop, network

    result: Dict[Type[Context], Dict[str, Tuple[str, COMMAND_FUNCTION, COMPLETER_FUNCTION]]] = {}
    for cmds, contexts, desc, func in commands:
        for context in contexts:
            for cmd in cmds:
                assert cmd not in result.setdefault(context, {})
                result[context][cmd] = (desc, func, completers.get(func))
    return result
