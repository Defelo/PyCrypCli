from ..commands.command import command, CTX_LOGIN
from ..game import Game


@command(["whoami"], ~CTX_LOGIN, "Print the name of the current user")
def handle_whoami(game: Game, *_):
    game.update_username()
    print(game.username)


@command(["status"], -1, "Indicate how many players are online")
def handle_status(game: Game, context: int, _):
    if context == CTX_LOGIN:
        online: int = game.client.status()["online"]
    else:
        online: int = game.client.info()["online"]
    print(f"Online players: {online}")
