import os
import time
from typing import List

from commands.command import command
from exceptions import *
from game import Game
from util import is_uuid


def stop_bruteforce(game: Game, service: dict):
    result: dict = game.client.bruteforce_stop(game.device_uuid, service["uuid"])
    target_device: str = result["target_device"]
    if result["access"]:
        if game.ask("Access granted. Do you want to connect to the device? [yes|no] ", ["yes", "no"]) == "yes":
            handle_connect(game, [target_device])
        else:
            print(f"To connect to the device type `connect {target_device}`")
    else:
        print("Access denied. The bruteforce attack was not successful")


def handle_bruteforce(game: Game, args: List[str]):
    duration: int = 20
    if len(args) in (1, 2) and args[0] in ("ssh", "telnet"):
        last_portscan = game.get_last_portscan()
        if last_portscan is None:
            print("You have to portscan your target first to find open ports.")
            return
        target_device, services = last_portscan
        for service in services:
            if service["name"] == args[0]:
                target_service: str = service["uuid"]
                break
        else:
            print(f"Service '{args[0]}' is not running on target device.")
            return
        if len(args) == 2:
            duration: str = args[1]
    elif len(args) in (2, 3):
        target_device: str = args[0]
        target_service: str = args[1]
        if not is_uuid(target_device):
            print("Invalid target device")
            return

        if not is_uuid(target_service):
            print("Invalid target service")
            return

        if len(args) == 3:
            duration: str = args[2]
    else:
        print("usage: service bruteforce <target-device> <target-service> [duration]")
        print("       service bruteforce ssh|telnet [duration]")
        return

    if isinstance(duration, str):
        if duration.isnumeric():
            duration: int = int(duration)
        else:
            print("Duration has to be a possible integer")
            return

    service: dict = game.get_service("bruteforce")
    if service is None:
        print("You have to create a bruteforce service before you can use it.")
        return

    result: dict = game.client.bruteforce_status(game.device_uuid, service["uuid"])
    if result["running"]:
        print(f"You are already attacking a device.")
        print("Target device: " + result["target_device"])
        print(f"Attack started {result['pen_time']:.0f} seconds ago")
        if game.ask("Do you want to stop this attack? [yes|no] ", ["yes", "no"]) == "yes":
            stop_bruteforce(game, service)
        return

    try:
        game.client.bruteforce_attack(
            game.device_uuid, service["uuid"],
            target_device, target_service
        )
    except ServiceNotFoundException:
        print("The target service does not exist.")
        return
    except TargetServiceNotRunningException:
        print("The target service is not running and cannot be exploited.")
        return

    print("You started a bruteforce attack")
    width: int = os.get_terminal_size().columns - 31
    steps: int = 17
    d: int = duration * steps
    i: int = 0
    try:
        for i in range(d):
            progress: int = int(i / d * width)
            j = i // steps
            text: str = f"\rBruteforcing {j // 60:02d}:{j % 60:02d} " + \
                        "[" + "=" * progress + ">" + " " * (width - progress) + "] " + \
                        f"({i / d * 100:.1f}%) "
            print(end=text, flush=True)
            time.sleep(1 / steps)
        i: int = (i + 1) // steps
        print(f"\rBruteforcing {i // 60:02d}:{i % 60:02d} [" + "=" * width + ">] (100%) ")
    except KeyboardInterrupt:
        print()
    stop_bruteforce(game, service)


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
        print("You have to create a portscan service before you can use it.")
        return

    result: dict = game.client.use_service(game.device_uuid, service["uuid"], target_device=target)
    services: List[dict] = result["services"]
    game.update_last_portscan((target, services))
    if not services:
        print("That device doesn't have any running services")
    for service in services:
        name: str = service["name"]
        uuid: str = service["uuid"]
        port: int = service["running_port"]
        print(f" - {name} on port {port} (UUID: {uuid})")


@command(["service"], "Create or use a service")
def handle_service(game: Game, args: List[str]):
    if len(args) < 1 or args[0] not in ("create", "list", "delete", "bruteforce", "portscan"):
        print("usage: service create|list|delete|bruteforce|portscan")
        return

    if args[0] == "create":
        if len(args) < 2 or args[1] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
            print("usage: service create bruteforce|portscan|telnet|ssh|miner")
            return

        extra: dict = {}
        if args[1] == "miner":
            if len(args) != 3:
                print("usage: service create miner <wallet>")
                return

            wallet_uuid: str = args[2]
            if not is_uuid(wallet_uuid):
                print("Invalid wallet uuid")
                return

            extra["wallet_uuid"] = wallet_uuid

        try:
            game.client.create_service(game.device_uuid, args[1], extra)
            print("Service was created")
        except AlreadyOwnThisServiceException:
            print("You already created this service")
    elif args[0] == "list":
        services: List[dict] = game.client.get_services(game.device_uuid)
        if services:
            print("Services:")
        else:
            print("There are no services on this device.")
        for service in services:
            name: str = service["name"]
            port: int = service["running_port"]
            line: str = f" - {name}"
            if port is not None:
                line += f" on port {port}"
            print(line)
    elif args[0] == "delete":
        if len(args) < 2 or args[1] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
            print("usage: service delete bruteforce|portscan|telnet|ssh|miner")
            return

        service: dict = game.get_service(args[1])
        if service is None:
            print(f"The service '{args[1]}' could not be found on this device")
            return

        game.client.delete_service(game.device_uuid, service["uuid"])

    elif args[0] == "bruteforce":
        handle_bruteforce(game, args[1:])
    elif args[0] == "portscan":
        handle_portscan(game, args[1:])


@command(["spot"], "Find a random device in the network")
def handle_spot(game: Game, *_):
    device: dict = game.client.spot()
    name: str = device["name"]
    uuid: str = device["uuid"]
    print(f"Name: '{name}'")
    print(f"UUID: {uuid}")
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

    print(f"Connecting to {uuid} ...")
    if game.client.part_owner(uuid):
        game.remote_login(uuid)
    else:
        print("Access denied")
