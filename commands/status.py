from commands.command import command
from game import Game


@command(["whoami"], "Print the name of the current user")
def handle_whoami(game: Game, *_):
    game.update_username()
    print(game.username)


@command(["status"], "Indicate how many players are online")
def handle_status(game: Game, *_):
    online: int = game.client.info()["online"]
    print(f"Online players: {online}")
