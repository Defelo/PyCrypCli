import os
import time
from typing import List, Tuple

from PyCrypCli.commands.command import command
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import DeviceContext, MainContext
from PyCrypCli.exceptions import *
from PyCrypCli.game_objects import Device, Service
from PyCrypCli.util import is_uuid


def stop_bruteforce(context: DeviceContext, service: Service):
    result: dict = context.get_client().bruteforce_stop(service.device, service.uuid)
    target_device: str = result["target_device"]
    if result["access"]:
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
        print("Unknown subcommand.")
    else:
        print_help(context, handle_service)


@handle_service.subcommand("create")
def handle_service_create(context: DeviceContext, args: List[str]):
    """
    Create a new service
    """

    if len(args) not in (1, 2) or args[0] not in ("bruteforce", "portscan", "telnet", "ssh", "miner"):
        print("usage: service create bruteforce|portscan|telnet|ssh|miner")
        return

    extra: dict = {}
    if args[0] == "miner":
        if len(args) != 2:
            print("usage: service create miner <wallet>")
            return

        try:
            wallet_uuid: str = context.get_wallet_from_file(args[1]).uuid
        except (
            FileNotFoundException,
            InvalidWalletFile,
            UnknownSourceOrDestinationException,
            PermissionDeniedException,
        ):
            if is_uuid(args[1]):
                wallet_uuid: str = args[1]
            else:
                print("Invalid wallet uuid")
                return

        extra["wallet_uuid"] = wallet_uuid

    try:
        context.get_client().create_service(context.host.uuid, args[0], extra)
        print("Service has been created")
    except AlreadyOwnThisServiceException:
        print("You already created this service")
    except WalletNotFoundException:
        print("Wallet does not exist.")


@handle_service.subcommand("list")
def handle_service_list(context: DeviceContext, _):
    """
    List all services installed on this device
    """

    services: List[Service] = context.get_client().get_services(context.host.uuid)
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
        print("usage: service delete bruteforce|portscan|telnet|ssh|miner")
        return

    service: Service = context.get_service(args[0])
    if service is None:
        print(f"The service '{args[0]}' could not be found on this device")
        return

    try:
        context.get_client().delete_service(service.device, service.uuid)
    except CannotDeleteEnforcedServiceException:
        print("The service could not be deleted.")


@handle_service.subcommand("start")
def handle_service_start(context: DeviceContext, args: List[str]):
    """
    Start a service
    """

    if len(args) != 1 or args[0] not in ("telnet", "ssh"):
        print("usage: service start telnet|ssh")
        return

    service: Service = context.get_service(args[0])
    if service is None:
        print(f"The service '{args[0]}' could not be found on this device")
        return
    elif service.running:
        print("This service is already running.")
        return

    try:
        context.get_client().toggle_service(service.device, service.uuid)
    except (CannotToggleDirectlyException, CouldNotStartService):
        print("The service could not be started.")


@handle_service.subcommand("stop")
def handle_service_stop(context: DeviceContext, args: List[str]):
    """
    Stop a service
    """

    if len(args) != 1 or args[0] not in ("telnet", "ssh"):
        print("usage: service stop telnet|ssh")
        return

    service: Service = context.get_service(args[0])
    if service is None:
        print(f"The service '{args[0]}' could not be found on this device")
        return
    elif not service.running:
        print("This service is not running.")
        return

    try:
        context.get_client().toggle_service(service.device, service.uuid)
    except CannotToggleDirectlyException:
        print("The service could not be stopped.")


@handle_service.subcommand("portscan")
def handle_portscan(context: DeviceContext, args: List[str]):
    """
    Perform a portscan
    """

    if len(args) != 1:
        print("usage: service portscan <device>")
        return

    target: str = args[0]
    if not is_uuid(target):
        print("Invalid target")
        return

    service: Service = context.get_service("portscan")
    if service is None:
        print("You have to create a portscan service before you can use it.")
        return

    result: dict = context.get_client().use_service(service.device, service.uuid, target_device=target)
    services: List[Service] = [Service.deserialize(s) for s in result["services"]]
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
        last_portscan: Tuple[str, List[Service]] = context.get_last_portscan()
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

    service: Service = context.get_service("bruteforce")
    if service is None:
        print("You have to create a bruteforce service before you can use it.")
        return

    result: dict = context.get_client().bruteforce_status(service.device, service.uuid)
    if result["running"]:
        print(f"You are already attacking a device.")
        print(f"Target device: {result['target_device']}")
        print(f"Attack started {result['pen_time']:.0f} seconds ago")
        if context.ask("Do you want to stop this attack? [yes|no] ", ["yes", "no"]) == "yes":
            stop_bruteforce(context, service)
        return

    try:
        context.get_client().bruteforce_attack(service.device, service.uuid, target_device, target_service)
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
        context.update_presence(
            state=f"Logged in: {context.username}@{context.root_context.host}",
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
    context.main_loop_presence()
    stop_bruteforce(context, service)


@handle_service_create.completer()
def service_create_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["bruteforce", "portscan", "ssh", "telnet", "miner"]
    elif len(args) == 2 and args[0] == "miner":
        return context.file_path_completer(args[2])


@handle_service_delete.completer()
def service_delete_completer(_, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["bruteforce", "portscan", "telnet", "miner"]


@handle_service_start.completer()
@handle_service_stop.completer()
@handle_bruteforce.completer()
def service_completer(_, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["ssh", "telnet"]


@command("spot", [DeviceContext])
def handle_spot(context: DeviceContext, _):
    """
    Find a random device in the network
    """

    device: Device = context.get_client().spot()
    print(f"Name: '{device.name}'" + " [hacked]" * context.get_client().part_owner(device.uuid))
    print(f"UUID: {device.uuid}")
    handle_portscan(context, [device.uuid])


@command("remote", [MainContext, DeviceContext])
def handle_remote(context: MainContext, args: List[str]):
    """
    Manage and connect to the devices you hacked before
    """

    if args:
        print("Unknown subcommand.")
    else:
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
        device: Device = context.get_client().device_info(name)
        if device is None:
            print("This device does not exist or you have no permission to access it.")
            return
    else:
        found_devices: List[Device] = []
        for device in context.get_hacked_devices():
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
    if context.get_client().part_owner(device.uuid):
        context.open(DeviceContext(context.root_context, context.session_token, device))
    else:
        print("This device does not exist or you have no permission to access it.")


@handle_remote_connect.completer()
def remote_completer(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        device_names: List[str] = [device.name for device in context.get_hacked_devices()]
        return [name for name in device_names if device_names.count(name) == 1]
