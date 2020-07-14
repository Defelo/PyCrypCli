from typing import List, Optional, Dict, Tuple

from PyCrypCli.commands import command, Command, CommandError
from PyCrypCli.context import LoginContext, MainContext, DeviceContext, Context


def print_help(context: Context, cmd: Optional[Command]):
    if cmd is None:
        cmds: Dict[str, Command] = {c.name: c for c in context.get_commands().values()}
    else:
        print(cmd.description)
        cmds: Dict[str, Command] = {c.name: c for c in cmd.prepared_subcommands.get(type(context), {}).values()}
    command_list: List[Tuple[str, str]] = [
        ("|".join([name] + cmd.aliases), cmd.description) for name, cmd in cmds.items()
    ]
    if not command_list:
        if cmd is None:
            print("No commands found.")
        return
    if cmd is not None:
        print()

    print(f"Available {'sub' * (cmd is not None)}commands:")
    max_length: int = max([len(cmd[0]) for cmd in command_list])
    for com, desc in command_list:
        com: str = com.ljust(max_length)
        print(f" - {com}    {desc}")


@command("help", [LoginContext, MainContext, DeviceContext])
def handle_main_help(context: Context, args: List[str]):
    """
    Show a list of available commands
    """

    if args:
        if args[0] in context.get_commands():
            cmd, args = context.get_commands()[args[0]].parse_command(context, args[1:])
            if not args:
                print_help(context, cmd)
                return

        raise CommandError("Command not found.")

    print_help(context, None)


@handle_main_help.completer()
def complete_help(context: Context, args: List[str]) -> List[str]:
    if len(args) == 1:
        return list(context.get_commands())

    if args[0] in context.get_commands():
        cmd, args = context.get_commands()[args[0]].parse_command(context, args[1:-1])
        if not args:
            return list(cmd.prepared_subcommands.get(type(context), {}))
