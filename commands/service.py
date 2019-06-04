from typing import List

from commands.command import command
from exceptions import *
from game import Game
from util import is_uuid


def handle_bruteforce(game: Game, args: List[str]):
    if len(args) != 2:
        print("usage: service bruteforce <target-device> <target-service>")
        return

    target_device: str = args[0]
    target_service: str = args[1]
    if not is_uuid(target_device):
        print("Invalid target device")
        return

    if not is_uuid(target_service):
        print("Invalid target service")
        return

    service: dict = game.get_service("bruteforce")
    if service is None:
        print("You have to create a bruteforce service before you use it")
        return

    try:
        result: dict = game.client.use_service(
            game.device_uuid, service["uuid"],
            target_device=target_device, target_service=target_service
        )
        assert result["ok"]
        if "access" in result:
            if result["access"]:
                print("Access granted - use `connect <device>`")
            else:
                print("Access denied. The bruteforce attack was not successful")
        else:
            print("You started a bruteforce attack")
    except UnknownServiceException:
        print("Unknown service. Attack couldn't be started.")


def handle_portscan(game: Game, args: List[str]):
    if len(args) != 1:
        print("usage: service portscan <device>")
        return

    target: str = args[0]
    if not is_uuid(target):
        print("Invalid target")
        return

    service: dict = game.get_service("portscan")
    if service is None:
        print("You have to create a portscan service before you use it")
        return

    result: dict = game.client.use_service(game.device_uuid, service["uuid"], target_device=target)
    if not result["services"]:
        print("That device doesn't have any running services")
    for service in result["services"]:
        name: str = service["name"]
        uuid: str = service["uuid"]
        port: int = service["running_port"]
        print(f" - {name} on port {port} (UUID: {uuid})")


@command(["service"], "Create or use a service")
def handle_service(game: Game, args: List[str]):
    if len(args) < 1 or args[0] not in ("create", "list", "bruteforce", "portscan"):
        print("usage: service create|list|bruteforce|portscan")
        return

    if args[0] == "create":
        if len(args) != 2 or args[1] not in ("bruteforce", "portscan", "telnet", "ssh"):
            print("usage: service create <bruteforce|portscan|telnet|ssh>")
            return

        try:
            game.client.create_service(game.device_uuid, args[1])
            print("Service was created")
        except AlreadyOwnServiceException:
            print("You already created this service")
    elif args[0] == "list":
        services: List[dict] = game.client.get_services(game.device_uuid)
        print("Services:")
        for service in services:
            name: str = service["name"]
            port: int = service["running_port"]
            line: str = f" - {name}"
            if port is not None:
                line += f" on port {port}"
            print(line)
    elif args[0] == "bruteforce":
        handle_bruteforce(game, args[1:])
    elif args[0] == "portscan":
        handle_portscan(game, args[1:])


@command(["spot"], "Find a random device in the network")
def handle_spot(game: Game, *_):
    device: dict = game.client.spot()
    name: str = device["name"]
    powered: bool = device["powered_on"]
    uuid: str = device["uuid"]
    powered_text: str = ["\033[38;2;255;51;51mno", "\033[38;2;100;246;23myes"][powered] + "\033[0m"
    print(f"Name: '{name}'")
    print(f"UUID: {uuid}")
    print(f"Powered on: {powered_text}")
    handle_portscan(game, [uuid])


@command(["connect"], "Connect to a device you hacked before")
def handle_connect(game: Game, args: List[str]):
    if len(args) != 1:
        print("usage: connect <device>")
        return

    uuid: str = args[0]
    if not is_uuid(uuid):
        print("Invalid device")
        return

    if game.client.part_owner(uuid):
        game.remote_login(uuid)
    else:
        print("Access denied")
