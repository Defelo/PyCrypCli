from typing import List, Dict, Optional

from PyCrypCli.commands import command, CommandError
from PyCrypCli.commands.help import print_help
from PyCrypCli.context import MainContext, DeviceContext
from PyCrypCli.exceptions import (
    AlreadyOwnADeviceException,
    DeviceNotFoundException,
    IncompatibleCPUSocket,
    NotEnoughRAMSlots,
    IncompatibleRAMTypes,
    IncompatibleDriverInterface,
)
from PyCrypCli.game_objects import Device, ResourceUsage, DeviceHardware, InventoryElement
from PyCrypCli.util import is_uuid


def get_device(context: MainContext, name_or_uuid: str, devices: Optional[List[Device]] = None) -> Device:
    if is_uuid(name_or_uuid):
        try:
            return Device.get_device(context.client, name_or_uuid)
        except DeviceNotFoundException:
            raise CommandError(f"There is no device with the uuid '{name_or_uuid}'.")
    else:
        found_devices: List[Device] = []
        for device in devices or Device.list_devices(context.client):
            if device.name == name_or_uuid:
                found_devices.append(device)
        if not found_devices:
            raise CommandError(f"There is no device with the name '{name_or_uuid}'.")
        if len(found_devices) > 1:
            raise CommandError(
                f"There is more than one device with the name '{name_or_uuid}'. You need to specify its UUID."
            )
        return found_devices[0]


@command("device", [MainContext, DeviceContext])
def handle_device(context: MainContext, args: List[str]):
    """
    Manage your devices
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_device)


@handle_device.subcommand("list")
def handle_device_list(context: MainContext, args: List[str]):
    """
    List your devices
    """

    if len(args) != 0:
        raise CommandError("usage: device list")

    devices: List[Device] = Device.list_devices(context.client)
    if not devices:
        print("You don't have any devices.")
    else:
        print("Your devices:")
    for device in devices:
        print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")


@handle_device.subcommand("create")
def handle_device_create(context: MainContext, args: List[str]):
    """
    Create your starter device
    """

    if len(args) != 0:
        raise CommandError("usage: device create")

    try:
        device: Device = Device.starter_device(context.client)
    except AlreadyOwnADeviceException:
        raise CommandError("You already own a device.")

    print("Your device has been created!")
    print(f"Hostname: {device.name} (UUID: {device.uuid})")


@handle_device.subcommand("build")
def handle_device_build(context: MainContext, args: List[str]):
    """
    Build a new device
    """

    if len(args) < 5:
        raise CommandError("usage: device build <mainboard> <cpu> <gpu> <ram> [<ram>...] <disk> [<disk>...]")

    hardware: dict = context.client.get_hardware_config()
    mainboard, cpu, gpu, *ram_and_disk = args
    ram: List[str] = []
    disk: List[str] = []

    for e in hardware["mainboards"]:
        if e.replace(" ", "") == mainboard:
            mainboard: str = e
            break
    else:
        print(f"'{mainboard}' is no mainboard.")
        return

    for e in hardware["cpu"]:
        if e.replace(" ", "") == cpu:
            cpu: str = e
            break
    else:
        print(f"'{cpu}' is no cpu.")
        return

    for e in hardware["gpu"]:
        if e.replace(" ", "") == gpu:
            gpu: str = e
            break
    else:
        print(f"'{gpu}' is no gpu.")
        return

    for element in ram_and_disk:
        for e in hardware["ram"]:
            if e.replace(" ", "") == element:
                ram.append(e)
                break
        else:
            for e in hardware["disk"]:
                if e.replace(" ", "") == element:
                    disk.append(e)
                    break
            else:
                print(f"'{element}' is neither ram nor disk.")
                return

    if not ram:
        raise CommandError("You have to chose at least one ram.")
    if not disk:
        raise CommandError("You have to chose at least one hard drive.")

    inventory: List[str] = [e.name for e in InventoryElement.list_inventory(context.client)]
    inventory_complete: bool = True
    for element in [mainboard, cpu, gpu] + ram + disk:
        if element in inventory:
            inventory.remove(element)
        else:
            print(f"'{element}' could not be found in your inventory.")
            inventory_complete: bool = False
    if not inventory_complete:
        return

    try:
        device: Device = Device.build(context.client, mainboard, cpu, gpu, ram, disk)
    except IncompatibleCPUSocket:
        raise CommandError("The mainboard socket is not compatible with the cpu.")
    except NotEnoughRAMSlots:
        raise CommandError("The mainboard has not enough ram slots.")
    except IncompatibleRAMTypes:
        raise CommandError("A ram type is incompatible with the mainboard.")
    except IncompatibleDriverInterface:
        raise CommandError("The drive interface is not compatible with the mainboard.")
    else:
        print("Your device has been created!")
        print(f"Hostname: {device.name} (UUID: {device.uuid})")


@handle_device.subcommand("boot")
def handle_device_boot(context: MainContext, args: List[str]):
    """
    Boot a device
    """

    if len(args) != 1:
        raise CommandError("usage: device boot <name|uuid>")

    device: Device = get_device(context, args[0])
    if device.powered_on:
        raise CommandError("This device is already powered on.")

    device.power()


@handle_device.subcommand("shutdown")
def handle_device_shutdown(context: MainContext, args: List[str]):
    """
    Shut down a device
    """

    if len(args) != 1:
        raise CommandError("usage: device shutdown <name|uuid>")

    device: Device = get_device(context, args[0])
    if not device.powered_on:
        raise CommandError("This device is not powered on.")

    device.power()


@handle_device.subcommand("connect")
def handle_device_connect(context: MainContext, args: List[str]):
    """
    Connect to one of your devices
    """

    if len(args) != 1:
        raise CommandError("usage: device connect <name|uuid>")

    device: Device = get_device(context, args[0])
    if not device.powered_on:
        raise CommandError("This device is not powered on.")

    context.open(DeviceContext(context.root_context, context.session_token, device))


@handle_device.subcommand("delete")
def handle_device_delete(context: MainContext, args: List[str]):
    """
    Delete a device
    """

    if len(args) != 1:
        raise CommandError("usage: device delete <name|uuid>")

    device: Device = get_device(context, args[0])

    device.delete()
    print("Device has been deleted.")


@handle_device_boot.completer()
@handle_device_shutdown.completer()
@handle_device_connect.completer()
@handle_device_delete.completer()
def complete_device(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        device_names: List[str] = [device.name for device in Device.list_devices(context.client)]
        return [name for name in device_names if device_names.count(name) == 1]
    return []


@handle_device_build.completer()
def complete_build(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return [name.replace(" ", "") for name in list(context.client.get_hardware_config()["mainboards"])]
    if len(args) == 2:
        return [name.replace(" ", "") for name in list(context.client.get_hardware_config()["cpu"])]
    if len(args) == 3:
        return [name.replace(" ", "") for name in list(context.client.get_hardware_config()["gpu"])]
    if len(args) == 4:
        return [name.replace(" ", "") for name in list(context.client.get_hardware_config()["ram"])]
    if len(args) >= 5:
        hardware: dict = context.client.get_hardware_config()
        return [name.replace(" ", "") for name in list(hardware["ram"]) + list(hardware["disk"])]
    return []


@command("hostname", [DeviceContext])
def handle_hostname(context: DeviceContext, args: List[str]):
    """
    Show or modify the name of the device
    """

    if args:
        name: str = " ".join(args)
        if not name:
            raise CommandError("The name must not be empty.")
        if len(name) > 15:
            raise CommandError("The name cannot be longer than 15 characters.")
        context.host.change_name(name)
    else:
        print(context.host.name)


@command("top", [DeviceContext])
def handle_top(context: DeviceContext, *_):
    """
    Display the current resource usage of this device
    """

    print(f"Resource usage of '{context.host.name}':")
    print()
    resource_usage: ResourceUsage = context.host.get_resource_usage()
    hardware: Dict[str, DeviceHardware] = {dh.hardware_type: dh for dh in context.host.get_hardware()}

    print(f"  Mainboard: {hardware['mainboard'].hardware_element}")
    print()

    print(f"  CPU: {hardware['cpu'].hardware_element}")
    print(f"    => Usage: {resource_usage.cpu * 100:.1f}%")
    print()

    print(f"  RAM: {hardware['ram'].hardware_element}")
    print(f"    => Usage: {resource_usage.ram * 100:.1f}%")
    print()

    if "gpu" in hardware:
        print(f"  GPU: {hardware['gpu'].hardware_element}")
        print(f"    => Usage: {resource_usage.gpu * 100:.1f}%")
        print()

    print(f"  Disk: {hardware['disk'].hardware_element}")
    print(f"    => Usage: {resource_usage.disk * 100:.1f}%")
    print()

    print("  Network:")
    print(f"    => Usage: {resource_usage.network * 100:.1f}%")
