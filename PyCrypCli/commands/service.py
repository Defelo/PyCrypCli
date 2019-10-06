import os
import time
from typing import List, Tuple

from ..commands.command import command, CTX_DEVICE, CTX_MAIN
from ..exceptions import *
from ..game import Game
from ..game_objects import Device, Service
from ..util import is_uuid


def stop_bruteforce(game: Game, service: Service):
    result: dict = game.client.bruteforce_stop(service.device, service.uuid)
    target_device: str = result["target_device"]
    if result["access"]:
        if game.ask("Access granted. Do you want to connect to the device? [yes|no] ", ["yes", "no"]) == "yes":
            handle_connect(game, CTX_DEVICE, ["connect", target_device])
        else:
            print(f"To connect to the device type `connect {target_device}`")
    else:
        print("Access denied. The bruteforce attack was not successful")


def handle_bruteforce(game: Game, args: List[str]):
    duration: int = 20
    if len(args) in (1, 2) and args[0] in ("ssh", "telnet"):
        last_portscan: Tuple[str, List[Service]] = game.get_last_portscan()
        if last_portscan is None:
            print("You have to portscan your target first to find open ports.")
            return
        target_device, services = last_portscan
        for service in services:
            if service.name == args[0]:
                target_service: str = service.uuid
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
            print("Duration has to be a positive integer")
            return

    service: Service = game.get_service("bruteforce")
    if service is None:
        print("You have to create a bruteforce service before you can use it.")
        return

    result: dict = game.client.bruteforce_status(service.device, service.uuid)
    if result["running"]:
        print(f"You are already attacking a device.")
        print(f"Target device: {result['target_device']}")
        print(f"Attack started {result['pen_time']:.0f} seconds ago")
        if game.ask("Do you want to stop this attack? [yes|no] ", ["yes", "no"]) == "yes":
            stop_bruteforce(game, service)
        return

    try:
        game.client.bruteforce_attack(service.device, service.uuid, target_device, target_service)
    except ServiceNotFoundException:
        print("The target service does not exist.")
        return
    except ServiceNotRunningException:
        print("The target service is not running and cannot be exploited.")
        return

    print("You started a bruteforce attack")
    width: int = os.get_terminal_size().columns - 31
    steps: int = 17
    d: int = duration * steps
    i: int = 0
    try:
        game.update_presence(
            state=f"Logged in: {game.username}@{game.host}",
            details="Hacking Remote Device",
            end=int(time.time()) + duration,
            large_image="cryptic",
            large_text="Cryptic",
        )
        for i in range(d):
            progress: int = int(i / d * width)
            j = i // steps
            text: str = f"\rBruteforcing {j // 60:02d}:{j % 60:02d} " + "[" + "=" * progress + ">" + " " * (
                width - progress
            ) + "] " + f"({i / d * 100:.1f}%) "
            print(end=text, flush=True)
            time.sleep(1 / steps)
        i: int = (i + 1) // steps
        print(f"\rBruteforcing {i // 60:02d}:{i % 60:02d} [" + "=" * width + ">] (100%) ")
    except KeyboardInterrupt:
        print()
    game.main_loop_presence()
    stop_bruteforce(game, service)


def handle_portscan(game: Game, args: List[str]):
    if len(args) != 1:
        print("usage: service portscan <device>")
        return

    target: str = args[0]
    if not is_uuid(target):
        print("Invalid target")
        return

    service: Service = game.get_service("portscan")
    if service is None:
        print("You have to create a portscan service before you can use it.")
        return

    result: dict = game.client.use_service(service.device, service.uuid, target_device=target)
    services: List[Service] = [Service.deserialize(s) for s in result["services"]]
    game.update_last_portscan((target, services))
    if not services:
        print("That device doesn't have any running services")
    for service in services:
        print(f" - {service.name} on port {service.running_port} (UUID: {service.uuid})")


@command(["service"], CTX_DEVICE, "Create or use a service")
def handle_service(game: Game, _, args: List[str]):
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

            try:
                wallet_uuid: str = game.get_wallet_from_file(args[2]).uuid
            except (
                FileNotFoundException,
                InvalidWalletFile,
                UnknownSourceOrDestinationException,
                PermissionDeniedException,
            ):
                if is_uuid(args[2]):
                    wallet_uuid: str = args[2]
                else:
                    print("Invalid wallet uuid")
                    return

            extra["wallet_uuid"] = wallet_uuid

        try:
            game.client.create_service(game.get_device().uuid, args[1], extra)
            print("Service has been created")
        except AlreadyOwnThisServiceException:
            print("You already created this service")
        except WalletNotFoundException:
            print("Wallet does not exist.")
    elif args[0] == "list":
        services: List[Service] = game.client.get_services(game.get_device().uuid)
        if not services:
            print("There are no services on this device.")
        else:
            print("Services:")
        for service in services:
            line: str = f" - {service.name}"
            if service.running_port is not None:
                line += f" on port {service.running_port}"
            print(line)
    elif args[0] == "delete":
        if len(args) < 2 or args[1] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
            print("usage: service delete bruteforce|portscan|telnet|ssh|miner")
            return

        service: Service = game.get_service(args[1])
        if service is None:
            print(f"The service '{args[1]}' could not be found on this device")
            return

        game.client.delete_service(service.device, service.uuid)

    elif args[0] == "bruteforce":
        handle_bruteforce(game, args[1:])
    elif args[0] == "portscan":
        handle_portscan(game, args[1:])


@command(["spot"], CTX_DEVICE, "Find a random device in the network")
def handle_spot(game: Game, *_):
    device: Device = game.client.spot()
    print(f"Name: '{device.name}'")
    print(f"UUID: {device.uuid}")
    handle_portscan(game, [device.uuid])


@command(["remote"], CTX_MAIN | CTX_DEVICE, "Manage and connect to the devices you hacked before")
def handle_connect(game: Game, _, args: List[str]):
    if not args:
        print("usage: remote list|connect")
        return

    if args[0] == "list":
        devices: List[Device] = game.get_hacked_devices()

        if not devices:
            print("You don't have access to any remote device.")
        else:
            print("Remote devices:")
        for device in devices:
            print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")
    elif args[0] == "connect":
        if len(args) != 2:
            print("usage: remote connect <name|uuid>")
            return

        name: str = args[1]
        if is_uuid(name):
            device: Device = game.client.device_info(name)
            if device is None:
                print("This device does not exist or you have no permission to access it.")
                return
        else:
            found_devices: List[Device] = []
            for device in game.get_hacked_devices():
                if device.name == name:
                    found_devices.append(device)

            if not found_devices:
                print(f"There is no device with the name '{name}'.")
                return
            elif len(found_devices) > 1:
                print(f"There is more than one device with the name '{name}'. You need to specify its UUID.")
                return

            device: Device = found_devices[0]

        print(f"Connecting to {device.name} (UUID: {device.uuid})")
        if game.client.part_owner(device.uuid):
            game.remote_login(device.uuid)
        else:
            print("This device does not exist or you have no permission to access it.")
    else:
        print("usage: remote list|connect")
