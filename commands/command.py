from typing import Callable, List, Tuple, Dict

from game import Game

MODULES: List[str] = ["status", "device", "files", "morphcoin", "service", "miner"]

COMMAND_FUNCTION = Callable[[Game, List[str]], None]
commands: List[Tuple[List[str], str, COMMAND_FUNCTION]] = []


def command(cmds: List[str], desc: str) -> Callable:
    def decorator(func: COMMAND_FUNCTION) -> COMMAND_FUNCTION:
        commands.append((cmds, desc, func))
        return func

    return decorator


def make_commands() -> Dict[str, Tuple[str, COMMAND_FUNCTION]]:
    for module in MODULES:
        __import__(f"commands.{module}")
    result: Dict[str, Tuple[str, COMMAND_FUNCTION]] = {}
    for cmds, desc, func in commands:
        for cmd in cmds:
            assert cmd not in result
            result[cmd] = (desc, func)
    return result
