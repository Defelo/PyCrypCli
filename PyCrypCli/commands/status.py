from PyCrypCli.commands.command import command
from PyCrypCli.context import MainContext, DeviceContext, LoginContext, Context


@command(["whoami"], [MainContext, DeviceContext], "Print the name of the current user")
def handle_whoami(context: MainContext, *_):
    print(f"{context.username} (UUID: {context.user_uuid})")


@command(["status"], [LoginContext, MainContext, DeviceContext], "Indicate how many players are online")
def handle_status(context: Context, _):
    if type(context) == LoginContext:
        online: int = context.get_client().status()["online"]
    else:
        online: int = context.get_client().info()["online"]
    print(f"Online players: {online}")
