from typing import List, Dict

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import MainContext, DeviceContext
from PyCrypCli.exceptions import AlreadyOwnADeviceException, DeviceNotFoundException
from PyCrypCli.game_objects import Device, ResourceUsage, DeviceHardware
from PyCrypCli.util import is_uuid


@command(["device"], [MainContext, DeviceContext], "Manage your devices")
def handle_device(context: MainContext, args: List[str]):
    if not args:
        print("usage: device list|create|connect")
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
    elif args[0] == "connect":
        if len(args) != 2:
            print("usage: device connect <name|uuid>")
            return

        name: str = args[1]
        if is_uuid(name):
            try:
                device: Device = context.get_client().device_info(name)
            except DeviceNotFoundException:
                print(f"There is no device with the uuid '{name}'.")
                return
        else:
            found_devices: List[Device] = []
            for device in context.get_client().get_devices():
                if device.name == name:
                    found_devices.append(device)
            if not found_devices:
                print(f"There is no device with the name '{name}'.")
                return
            elif len(found_devices) > 1:
                print(f"There is more than one device with the name '{name}'. You need to specify its UUID.")
                return
            device: Device = found_devices[0]

        context.open(DeviceContext(context.root_context, context.session_token, device))
    else:
        print("usage: device list|create|connect")


@completer([handle_device])
def complete_device(context: MainContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return ["list", "create", "connect"]
    elif len(args) == 2:
        device_names: List[str] = [device.name for device in context.get_client().get_devices()]
        return [name for name in device_names if device_names.count(name) == 1]


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

    print(f"  GPU: {hardware['gpu'].hardware_element}")
    print(f"    => Usage: {resource_usage.gpu * 100:.1f}%")
    print()

    print(f"  Disk: {hardware['disk'].hardware_element}")
    print(f"    => Usage: {resource_usage.disk * 100:.1f}%")
    print()

    print(f"  Network:")
    print(f"    => Usage: {resource_usage.network * 100:.1f}%")
