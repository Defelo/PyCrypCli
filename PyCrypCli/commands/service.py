import os
import time
from typing import List, Tuple

from PyCrypCli.commands import command, CommandError
from PyCrypCli.commands.help import print_help
from PyCrypCli.commands.morphcoin import get_wallet_from_file
from PyCrypCli.context import DeviceContext, MainContext
from PyCrypCli.exceptions import (
    ServiceNotFoundException,
    AttackNotRunningException,
    AlreadyOwnThisServiceException,
    WalletNotFoundException,
    CannotDeleteEnforcedServiceException,
    CannotToggleDirectlyException,
    CouldNotStartService,
    ServiceNotRunningException,
)
from PyCrypCli.game_objects import Device, Service, PortscanService, BruteforceService, PublicService
from PyCrypCli.util import is_uuid


def get_service(context: DeviceContext, name: str) -> Service:
    try:
        return context.host.get_service_by_name(name)
    except ServiceNotFoundException:
        raise CommandError(f"The service '{name}' could not be found on this device")


def stop_bruteforce(context: DeviceContext, service: BruteforceService):
    try:
        access, _, target_device = service.stop()
    except AttackNotRunningException:
        raise CommandError("Bruteforce attack is not running.")
    if access:
        if context.ask("Access granted. Do you want to connect to the device? [yes|no] ", ["yes", "no"]) == "yes":
            handle_remote_connect(context, [target_device])
        else:
            print(f"To connect to the device type `remote connect {target_device}`")
    else:
        print("Access denied. The bruteforce attack was not successful")


@command("service", [DeviceContext])
def handle_service(context: DeviceContext, args: List[str]):
    """
    Create or use a service
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_service)


@handle_service.subcommand("create")
def handle_service_create(context: DeviceContext, args: List[str]):
    """
    Create a new service
    """

    if len(args) not in (1, 2) or args[0] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
        raise CommandError("usage: service create bruteforce|portscan|telnet|ssh|miner")

    extra: dict = {}
    if args[0] == "miner":
        if len(args) != 2:
            raise CommandError("usage: service create miner <wallet>")

        try:
            wallet_uuid: str = get_wallet_from_file(context, args[1]).uuid
        except CommandError:
            if is_uuid(args[1]):
                wallet_uuid: str = args[1]
            else:
                raise CommandError("Invalid wallet uuid")

        extra["wallet_uuid"] = wallet_uuid

    try:
        context.host.create_service(args[0], **extra)
        print("Service has been created")
    except AlreadyOwnThisServiceException:
        raise CommandError("You already created this service")
    except WalletNotFoundException:
        raise CommandError("Wallet does not exist.")


@handle_service.subcommand("list")
def handle_service_list(context: DeviceContext, _):
    """
    List all services installed on this device
    """

    services: List[Service] = context.host.get_services()
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
def handle_service_delete(context: DeviceContext, args: List[str]):
    """
    Delete a service
    """

    if len(args) != 1 or args[0] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
        raise CommandError("usage: service delete bruteforce|portscan|telnet|ssh|miner")

    service: Service = get_service(context, args[0])

    try:
        service.delete()
    except CannotDeleteEnforcedServiceException:
        raise CommandError("The service could not be deleted.")


@handle_service.subcommand("start")
def handle_service_start(context: DeviceContext, args: List[str]):
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
    except (CannotToggleDirectlyException, CouldNotStartService):
        raise CommandError("The service could not be started.")


@handle_service.subcommand("stop")
def handle_service_stop(context: DeviceContext, args: List[str]):
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
    except CannotToggleDirectlyException:
        raise CommandError("The service could not be stopped.")


@handle_service.subcommand("portscan")
def handle_portscan(context: DeviceContext, args: List[str]):
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
    except ServiceNotFoundException:
        raise CommandError("You have to create a portscan service before you can use it.")

    services: List[PublicService] = service.scan(target)
    context.update_last_portscan((target, services))
    if not services:
        print("That device doesn't have any running services")
    for service in services:
        print(f" - {service.name} on port {service.running_port} (UUID: {service.uuid})")


@handle_service.subcommand("bruteforce")
def handle_bruteforce(context: DeviceContext, args: List[str]):
    """
    Start a bruteforce attack
    """

    duration: int = 20
    if len(args) in (1, 2) and args[0] in ("ssh", "telnet"):
        last_portscan: Tuple[str, List[PublicService]] = context.get_last_portscan()
        if last_portscan is None:
            raise CommandError("You have to portscan your target first to find open ports.")
        target_device, services = last_portscan
        for service in services:
            if service.name == args[0]:
                target_service: str = service.uuid
                break
        else:
            raise CommandError(f"Service '{args[0]}' is not running on target device.")
        if len(args) == 2:
            duration: str = args[1]
    elif len(args) in (2, 3):
        target_device: str = args[0]
        target_service: str = args[1]
        if not is_uuid(target_device):
            raise CommandError("Invalid target device")
        if not is_uuid(target_service):
            raise CommandError("Invalid target service")

        if len(args) == 3:
            duration: str = args[2]
    else:
        raise CommandError(
            "usage: service bruteforce <target-device> <target-service> [duration]\n"
            "       service bruteforce ssh|telnet [duration]"
        )

    if isinstance(duration, str):
        if duration.isnumeric():
            duration: int = int(duration)
        else:
            raise CommandError("Duration has to be a positive integer")

    try:
        service: BruteforceService = BruteforceService.get_bruteforce_service(context.client, context.host.uuid)
    except ServiceNotFoundException:
        raise CommandError("You have to create a bruteforce service before you can use it.")

    if service.running:
        print("You are already attacking a device.")
        print(f"Target device: {service.target_device}")
        if context.ask("Do you want to stop this attack? [yes|no] ", ["yes", "no"]) == "yes":
            stop_bruteforce(context, service)
        return

    try:
        service.attack(target_device, target_service)
    except ServiceNotFoundException:
        raise CommandError("The target service does not exist.")
    except ServiceNotRunningException:
        raise CommandError("The target service is not running and cannot be exploited.")

    print("You started a bruteforce attack")
    width: int = os.get_terminal_size().columns - 31
    steps: int = 17
    d: int = duration * steps
    i: int = 0
    last_check = 0
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
                service.update()
                if not service.running:
                    print("\rBruteforce attack has been aborted.")
                    return

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
    context.main_loop_presence()
    stop_bruteforce(context, service)


@handle_service_create.completer()
def service_create_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["bruteforce", "portscan", "ssh", "telnet", "miner"]
    if len(args) == 2 and args[0] == "miner":
        return context.file_path_completer(args[1])
    return []


@handle_service_delete.completer()
def service_delete_completer(_, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["bruteforce", "portscan", "telnet", "miner"]
    return []


@handle_service_start.completer()
@handle_service_stop.completer()
@handle_bruteforce.completer()
def service_completer(_, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["ssh", "telnet"]
    return []


@command("spot", [DeviceContext])
def handle_spot(context: DeviceContext, _):
    """
    Find a random device in the network
    """

    device: Device = Device.spot(context.client)
    print(f"Name: '{device.name}'" + " [hacked]" * device.part_owner())
    print(f"UUID: {device.uuid}")
    handle_portscan(context, [device.uuid])


@command("remote", [MainContext, DeviceContext])
def handle_remote(context: MainContext, args: List[str]):
    """
    Manage and connect to the devices you hacked before
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_remote)


@handle_remote.subcommand("list")
def handle_remote_list(context: MainContext, _):
    """
    List remote devices
    """

    devices: List[Device] = context.get_hacked_devices()

    if not devices:
        print("You don't have access to any remote device.")
    else:
        print("Remote devices:")
    for device in devices:
        print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")


@handle_remote.subcommand("connect")
def handle_remote_connect(context: MainContext, args: List[str]):
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
        found_devices: List[Device] = []
        for device in context.get_hacked_devices():
            if device.name == name:
                found_devices.append(device)

        if not found_devices:
            raise CommandError(f"There is no device with the name '{name}'.")
        if len(found_devices) > 1:
            raise CommandError(f"There is more than one device with the name '{name}'. You need to specify its UUID.")

        device: Device = found_devices[0]

    print(f"Connecting to {device.name} (UUID: {device.uuid})")
    if device.part_owner():
        context.open(DeviceContext(context.root_context, context.session_token, device))
    else:
        raise CommandError("This device does not exist or you have no permission to access it.")


@handle_remote_connect.completer()
def remote_completer(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        device_names: List[str] = [device.name for device in context.get_hacked_devices()]
        return [name for name in device_names if device_names.count(name) == 1]
    return []
