from typing import Callable, List, Tuple, Dict

from ..game import Game

CTX_LOGIN = 1
CTX_MAIN = 2
CTX_DEVICE = 4

COMMAND_FUNCTION = Callable[[Game, int, List[str]], None]
commands: [Tuple[List[str], int, str, COMMAND_FUNCTION]] = []


def command(cmds: List[str], context: int, desc: str) -> Callable:
    def decorator(func: COMMAND_FUNCTION) -> COMMAND_FUNCTION:
        commands.append((cmds, context, desc, func))
        return func

    return decorator


def make_commands() -> Dict[int, Dict[str, Tuple[str, COMMAND_FUNCTION]]]:
    # noinspection PyUnresolvedReferences
    from . import status, device, files, morphcoin, service, miner

    result: Dict[int, Dict[str, Tuple[str, COMMAND_FUNCTION]]] = {}
    for ctx in [CTX_LOGIN, CTX_MAIN, CTX_DEVICE]:
        for cmds, context, desc, func in commands:
            if not ctx & context:
                continue
            for cmd in cmds:
                assert cmd not in result.setdefault(ctx, {})
                result[ctx][cmd] = (desc, func)
    return result
