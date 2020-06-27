from typing import List, Dict, Optional

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import MainContext, DeviceContext
from PyCrypCli.exceptions import (
    AlreadyOwnADeviceException,
    DeviceNotFoundException,
    IncompatibleCPUSocket,
    NotEnoughRAMSlots,
    IncompatibleRAMTypes,
    IncompatibleDriverInterface,
)
from PyCrypCli.game_objects import Device, ResourceUsage, DeviceHardware
from PyCrypCli.util import is_uuid


def get_device(context: MainContext, name_or_uuid: str, devices: Optional[List[Device]] = None) -> Optional[Device]:
    if is_uuid(name_or_uuid):
        try:
            return context.get_client().device_info(name_or_uuid)
        except DeviceNotFoundException:
            print(f"There is no device with the uuid '{name_or_uuid}'.")
            return None
    else:
        found_devices: List[Device] = []
        for device in devices or context.get_client().get_devices():
            if device.name == name_or_uuid:
                found_devices.append(device)
        if not found_devices:
            print(f"There is no device with the name '{name_or_uuid}'.")
            return None
        elif len(found_devices) > 1:
            print(f"There is more than one device with the name '{name_or_uuid}'. You need to specify its UUID.")
            return None
        return found_devices[0]


@command(["device"], [MainContext, DeviceContext], "Manage your devices")
def handle_device(context: MainContext, args: List[str]):
    if not args:
        print("usage: device list|create|build|boot|shutdown|connect|delete")
        return

    if args[0] == "list":
        if len(args) != 1:
            print("usage: device list")
            return

        devices: List[Device] = context.get_client().get_devices()
        if not devices:
            print("You don't have any devices.")
        else:
            print("Your devices:")
        for device in devices:
            print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")
    elif args[0] == "create":
        if len(args) != 1:
            print("usage: device create")
            return

        try:
            device: Device = context.get_client().create_starter_device()
        except AlreadyOwnADeviceException:
            print("You already own a device.")
            return

        print("Your device has been created!")
        print(f"Hostname: {device.name} (UUID: {device.uuid})")
    elif args[0] == "build":
        if len(args) < 6:
            print("usage: device build <mainboard> <cpu> <gpu> <ram> [<ram>...] <disk> [<disk>...]")
            return

        hardware: dict = context.get_client().get_hardware_config()
        mainboard, cpu, gpu, *ram_and_disk = args[1:]
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
            print("You have to chose at least one ram.")
            return
        elif not disk:
            print("You have to chose at least one hard drive.")
            return

        inventory: List[str] = [e.element_name for e in context.get_client().inventory_list()]
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
            device: Device = context.get_client().build_device(mainboard, cpu, gpu, ram, disk)
        except IncompatibleCPUSocket:
            print("The mainboard socket is not compatible with the cpu.")
        except NotEnoughRAMSlots:
            print("The mainboard has not enough ram slots.")
        except IncompatibleRAMTypes:
            print("A ram type is incompatible with the mainboard.")
        except IncompatibleDriverInterface:
            print("The drive interface is not compatible with the mainboard.")
        else:
            print("Your device has been created!")
            print(f"Hostname: {device.name} (UUID: {device.uuid})")
    elif args[0] == "boot":
        if len(args) != 2:
            print("usage: device boot <name|uuid>")
            return

        device: Optional[Device] = get_device(context, args[1])
        if device is None:
            return
        elif device.powered_on:
            print("This device is already powered on.")
            return

        context.get_client().device_power(device.uuid)
    elif args[0] == "shutdown":
        if len(args) != 2:
            print("usage: device shutdown <name|uuid>")
            return

        device: Optional[Device] = get_device(context, args[1])
        if device is None:
            return
        elif not device.powered_on:
            print("This device is not powered on.")
            return

        context.get_client().device_power(device.uuid)
    elif args[0] == "connect":
        if len(args) != 2:
            print("usage: device connect <name|uuid>")
            return

        device: Optional[Device] = get_device(context, args[1])
        if device is None:
            return

        if not device.powered_on:
            print("This device is not powered on.")
            return

        context.open(DeviceContext(context.root_context, context.session_token, device))
    elif args[0] == "delete":
        if len(args) != 2:
            print("usage: device delete <name|uuid>")
            return

        device: Optional[Device] = get_device(context, args[1])
        if device is None:
            return

        context.get_client().delete_device(device.uuid)
        print("Device has been deleted.")
    else:
        print("usage: device list|create|build|boot|shutdown|connect|delete")


@completer([handle_device])
def complete_device(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["list", "create", "build", "boot", "shutdown", "connect", "delete"]
    elif len(args) == 2:
        if args[0] in ("boot", "shutdown", "connect", "delete"):
            device_names: List[str] = [device.name for device in context.get_client().get_devices()]
            return [name for name in device_names if device_names.count(name) == 1]
        elif args[0] == "build":
            return [name.replace(" ", "") for name in list(context.get_client().get_hardware_config()["mainboards"])]
    elif len(args) == 3:
        if args[0] == "build":
            return [name.replace(" ", "") for name in list(context.get_client().get_hardware_config()["cpu"])]
    elif len(args) == 4:
        if args[0] == "build":
            return [name.replace(" ", "") for name in list(context.get_client().get_hardware_config()["gpu"])]
    elif len(args) == 5:
        if args[0] == "build":
            return [name.replace(" ", "") for name in list(context.get_client().get_hardware_config()["ram"])]
    elif len(args) >= 6:
        if args[0] == "build":
            hardware: dict = context.get_client().get_hardware_config()
            return [name.replace(" ", "") for name in list(hardware["ram"]) + list(hardware["disk"])]


@command(["hostname"], [DeviceContext], "Show or modify the name of the device")
def handle_hostname(context: DeviceContext, args: List[str]):
    if args:
        name: str = " ".join(args)
        if not name:
            print("The name must not be empty.")
            return
        if len(name) > 15:
            print("The name cannot be longer than 15 characters.")
            return
        context.get_client().change_device_name(context.host.uuid, name)
    else:
        print(context.host.name)


@command(["top"], [DeviceContext], "Display the current resource usage of this device")
def handle_top(context: DeviceContext, *_):
    print(f"Resource usage of '{context.host.name}':")
    print()
    resource_usage: ResourceUsage = context.get_client().hardware_resources(context.host.uuid)
    hardware: Dict[str, DeviceHardware] = {
        dh.hardware_type: dh for dh in (context.get_client().get_device_hardware(context.host.uuid))
    }

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

    print(f"  Network:")
    print(f"    => Usage: {resource_usage.network * 100:.1f}%")
