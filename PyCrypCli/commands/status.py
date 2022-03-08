from typing import Any

from .command import command
from ..context import MainContext, DeviceContext, LoginContext, Context


@command("whoami", [MainContext, DeviceContext])
def handle_whoami(context: MainContext, _: Any) -> None:
    """
    Print the name of the current user
    """

    print(f"{context.username} (UUID: {context.user_uuid})")


@command("status", [LoginContext, MainContext, DeviceContext])
def handle_status(context: Context, _: Any) -> None:
    """
    Indicate how many players are online
    """

    if type(context) is LoginContext:
        online: int = context.client.status().online
    else:
        online = context.client.info().online
    print(f"Online players: {online}")
