from PyCrypCli.commands.command import command
from PyCrypCli.context import MainContext, DeviceContext, LoginContext, Context


@command("whoami", [MainContext, DeviceContext])
def handle_whoami(context: MainContext, *_):
    """
    Print the name of the current user
    """

    print(f"{context.username} (UUID: {context.user_uuid})")


@command("status", [LoginContext, MainContext, DeviceContext])
def handle_status(context: Context, _):
    """
    Indicate how many players are online
    """

    if type(context) == LoginContext:
        online: int = context.get_client().status()["online"]
    else:
        online: int = context.get_client().info()["online"]
    print(f"Online players: {online}")
