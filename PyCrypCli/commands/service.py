import os
import time
from typing import Any, cast

from .command import command, CommandError
from .help import print_help
from .morphcoin import get_wallet_from_file
from ..context import DeviceContext, MainContext
from ..exceptions import (
    ServiceNotFoundError,
    AttackNotRunningError,
    AlreadyOwnThisServiceError,
    WalletNotFoundError,
    CannotDeleteEnforcedServiceError,
    CannotToggleDirectlyError,
    CouldNotStartServiceError,
    ServiceNotRunningError,
)
from ..models import Device, Service, PortscanService, BruteforceService, PublicService
from ..util import is_uuid


def get_service(context: DeviceContext, name: str) -> Service:
    try:
        return context.host.get_service_by_name(name)
    except ServiceNotFoundError:
        raise CommandError(f"The service '{name}' could not be found on this device")


def stop_bruteforce(context: DeviceContext, service: BruteforceService) -> None:
    try:
        access, _, target_device = service.stop()
    except AttackNotRunningError:
        raise CommandError("Bruteforce attack is not running.")
    if access:
        if context.ask("Access granted. Do you want to connect to the device? [yes|no] ", ["yes", "no"]) == "yes":
            handle_remote_connect(context, [target_device])
        else:
            print(f"To connect to the device type `remote connect {target_device}`")
    else:
        print("Access denied. The bruteforce attack was not successful")


@command("service", [DeviceContext])
def handle_service(context: DeviceContext, args: list[str]) -> None:
    """
    Create or use a service
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_service)


@handle_service.subcommand("create")
def handle_service_create(context: DeviceContext, args: list[str]) -> None:
    """
    Create a new service
    """

    if len(args) not in (1, 2) or args[0] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
        raise CommandError("usage: service create bruteforce|portscan|telnet|ssh|miner")

    extra: dict[str, Any] = {}
    if args[0] == "miner":
        if len(args) != 2:
            raise CommandError("usage: service create miner <wallet>")

        try:
            wallet_uuid: str = get_wallet_from_file(context, args[1]).uuid
        except CommandError:
            if is_uuid(args[1]):
                wallet_uuid = args[1]
            else:
                raise CommandError("Invalid wallet uuid")

        extra["wallet_uuid"] = wallet_uuid

    try:
        context.host.create_service(args[0], **extra)
        print("Service has been created")
    except AlreadyOwnThisServiceError:
        raise CommandError("You already created this service")
    except WalletNotFoundError:
        raise CommandError("Wallet does not exist.")


@handle_service.subcommand("list")
def handle_service_list(context: DeviceContext, _: Any) -> None:
    """
    List all services installed on this device
    """

    services: list[Service] = context.host.get_services()
    if not services:
        print("There are no services on this device.")
    else:
        print("Services:")
    for service in services:
        line: str = f" - [{['stopped', 'running'][service.running]}] {service.name}"
        if service.running_port is not None:
            line += f" on port {service.running_port}"
        print(line)


@handle_service.subcommand("delete")
def handle_service_delete(context: DeviceContext, args: list[str]) -> None:
    """
    Delete a service
    """

    if len(args) != 1 or args[0] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
        raise CommandError("usage: service delete bruteforce|portscan|telnet|ssh|miner")

    service: Service = get_service(context, args[0])

    try:
        service.delete()
    except CannotDeleteEnforcedServiceError:
        raise CommandError("The service could not be deleted.")


@handle_service.subcommand("start")
def handle_service_start(context: DeviceContext, args: list[str]) -> None:
    """
    Start a service
    """

    if len(args) != 1 or args[0] not in ("telnet", "ssh"):
        raise CommandError("usage: service start telnet|ssh")

    service: Service = get_service(context, args[0])
    if service.running:
        raise CommandError("This service is already running.")

    try:
        service.toggle()
    except (CannotToggleDirectlyError, CouldNotStartServiceError):
        raise CommandError("The service could not be started.")


@handle_service.subcommand("stop")
def handle_service_stop(context: DeviceContext, args: list[str]) -> None:
    """
    Stop a service
    """

    if len(args) != 1 or args[0] not in ("telnet", "ssh"):
        raise CommandError("usage: service stop telnet|ssh")

    service: Service = get_service(context, args[0])
    if not service.running:
        raise CommandError("This service is not running.")

    try:
        service.toggle()
    except CannotToggleDirectlyError:
        raise CommandError("The service could not be stopped.")


@handle_service.subcommand("portscan")
def handle_portscan(context: DeviceContext, args: list[str]) -> None:
    """
    Perform a portscan
    """

    if len(args) != 1:
        raise CommandError("usage: service portscan <device>")

    target: str = args[0]
    if not is_uuid(target):
        raise CommandError("Invalid target")

    try:
        service: PortscanService = PortscanService.get_portscan_service(context.client, context.host.uuid)
    except ServiceNotFoundError:
        raise CommandError("You have to create a portscan service before you can use it.")

    services: list[PublicService] = service.scan(target)
    context.last_portscan = target, services
    if not services:
        print("That device doesn't have any running services")
    for s in services:
        print(f" - {s.name} on port {s.running_port} (UUID: {s.uuid})")


@handle_service.subcommand("bruteforce")
def handle_bruteforce(context: DeviceContext, args: list[str]) -> None:
    """
    Start a bruteforce attack
    """

    duration_arg: str = "100%"
    duration: int = 0
    chance: float | None = None
    if len(args) in (1, 2) and args[0] in ("ssh", "telnet"):
        if context.last_portscan is None:
            raise CommandError("You have to portscan your target first to find open ports.")

        target_device, services = context.last_portscan
        for service in services:
            if service.name == args[0]:
                target_service: str = service.uuid
                break
        else:
            raise CommandError(f"Service '{args[0]}' is not running on target device.")
        if len(args) == 2:
            duration_arg = args[1]
    elif len(args) in (2, 3):
        target_device = args[0]
        target_service = args[1]
        if not is_uuid(target_device):
            raise CommandError("Invalid target device")
        if not is_uuid(target_service):
            raise CommandError("Invalid target service")

        if len(args) == 3:
            duration_arg = args[2]
    else:
        raise CommandError(
            "usage: service bruteforce <target-device> <target-service> [duration|success_chance]\n"
            "       service bruteforce ssh|telnet [duration|success_chance]"
        )

    if duration_arg.endswith("%"):
        error = "Success chance has to be a positive number between 0 and 100"
        try:
            chance = float(duration_arg[:-1]) / 100
        except ValueError:
            raise CommandError(error)
        if chance < 0 or chance > 1:
            raise CommandError(error)
    else:
        if not duration_arg.isnumeric():
            raise CommandError("Duration has to be a positive integer")
        duration = int(duration_arg)

    try:
        bruteforce_service: BruteforceService = BruteforceService.get_bruteforce_service(
            context.client, context.host.uuid
        )
    except ServiceNotFoundError:
        raise CommandError("You have to create a bruteforce service before you can use it.")

    if bruteforce_service.running:
        print("You are already attacking a device.")
        print(f"Target device: {bruteforce_service.target_device_uuid}")
        if context.ask("Do you want to stop this attack? [yes|no] ", ["yes", "no"]) == "yes":
            stop_bruteforce(context, bruteforce_service)
        return

    try:
        bruteforce_service.attack(target_device, target_service)
        if chance is not None:
            bruteforce_service.update()
            duration = round((chance + 0.1) * 20 / bruteforce_service.speed)
    except ServiceNotFoundError:
        raise CommandError("The target service does not exist.")
    except ServiceNotRunningError:
        raise CommandError("The target service is not running and cannot be exploited.")

    print("You started a bruteforce attack")
    width = os.get_terminal_size().columns - 31
    steps = 17
    d = duration * steps
    i = 0
    last_check: float = 0
    try:
        context.update_presence(
            state=f"Logged in: {context.username}@{context.root_context.host}",
            details="Hacking Remote Device",
            end=int(time.time()) + duration,
            large_image="cryptic",
            large_text="Cryptic",
        )
        for i in range(d):
            if time.time() - last_check > 1:
                last_check = time.time()
                bruteforce_service.update()
                if not bruteforce_service.running:
                    print("\rBruteforce attack has been aborted.")
                    return

            progress: int = int(i / d * width)
            j = i // steps
            progress_bar = "[" + "=" * progress + ">" + " " * (width - progress) + "]"
            text = f"\rBruteforcing {j // 60:02d}:{j % 60:02d} {progress_bar} ({i / d * 100:.1f}%) "
            print(end=text, flush=True)
            time.sleep(1 / steps)
        i = (i + 1) // steps
        print(f"\rBruteforcing {i // 60:02d}:{i % 60:02d} [" + "=" * width + ">] (100%) ")
    except KeyboardInterrupt:
        print()
    context.main_loop_presence()
    stop_bruteforce(context, bruteforce_service)


@handle_service_create.completer()
def service_create_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return ["bruteforce", "portscan", "ssh", "telnet", "miner"]
    if len(args) == 2 and args[0] == "miner":
        return context.file_path_completer(args[1])
    return []


@handle_service_delete.completer()
def service_delete_completer(_: Any, args: list[str]) -> list[str]:
    if len(args) == 1:
        return ["bruteforce", "portscan", "telnet", "miner"]
    return []


@handle_service_start.completer()
@handle_service_stop.completer()
@handle_bruteforce.completer()
def service_completer(_: Any, args: list[str]) -> list[str]:
    if len(args) == 1:
        return ["ssh", "telnet"]
    return []


@command("spot", [DeviceContext])
def handle_spot(context: DeviceContext, _: Any) -> None:
    """
    Find a random device in the network
    """

    device: Device = Device.spot(context.client)
    print(f"Name: '{device.name}'" + " [hacked]" * device.part_owner())
    print(f"UUID: {device.uuid}")
    handle_portscan(context, [device.uuid])


@command("remote", [MainContext, DeviceContext])
def handle_remote(context: MainContext, args: list[str]) -> None:
    """
    Manage and connect to the devices you hacked before
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_remote)


@handle_remote.subcommand("list")
def handle_remote_list(context: MainContext, _: Any) -> None:
    """
    List remote devices
    """

    devices: list[Device] = context.get_hacked_devices()

    if not devices:
        print("You don't have access to any remote device.")
    else:
        print("Remote devices:")
    for device in devices:
        print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")


@handle_remote.subcommand("connect")
def handle_remote_connect(context: MainContext, args: list[str]) -> None:
    """
    Connect to a remote device
    """

    if len(args) != 1:
        print("usage: remote connect <name|uuid>")
        return

    name: str = args[0]
    if is_uuid(name):
        device: Device = Device.get_device(context.client, name)
        if device is None:
            raise CommandError("This device does not exist or you have no permission to access it.")
    else:
        found_devices: list[Device] = []
        for device in context.get_hacked_devices():
            if device.name == name:
                found_devices.append(device)

        if not found_devices:
            raise CommandError(f"There is no device with the name '{name}'.")
        if len(found_devices) > 1:
            raise CommandError(f"There is more than one device with the name '{name}'. You need to specify its UUID.")

        device = found_devices[0]

    print(f"Connecting to {device.name} (UUID: {device.uuid})")
    if device.part_owner():
        context.open(DeviceContext(context.root_context, cast(str, context.session_token), device))
    else:
        raise CommandError("This device does not exist or you have no permission to access it.")


@handle_remote_connect.completer()
def remote_completer(context: MainContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        device_names: list[str] = [device.name for device in context.get_hacked_devices()]
        return [name for name in device_names if device_names.count(name) == 1]
    return []
