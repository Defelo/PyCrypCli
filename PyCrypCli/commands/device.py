from typing import List

from ..commands.command import command, CTX_DEVICE, CTX_MAIN
from ..exceptions import AlreadyOwnADeviceException, DeviceNotFoundException
from ..game import Game
from ..game_objects import Device
from ..util import is_uuid


@command(["device"], CTX_MAIN | CTX_DEVICE, "Manage your devices")
def handle_device(game: Game, _, args: List[str]):
    if not args:
        print("usage: device list|create|connect")
        return

    if args[0] == "list":
        if len(args) != 1:
            print("usage: device list")
            return

        devices: List[Device] = game.client.get_devices()
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
            device: Device = game.client.create_starter_device()
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
                device: Device = game.client.device_info(name)
            except DeviceNotFoundException:
                print(f"There is no device with the uuid '{name}'.")
                return
        else:
            found_devices: List[Device] = []
            for device in game.client.get_devices():
                if device.name == name:
                    found_devices.append(device)
            if not found_devices:
                print(f"There is no device with the name '{name}'.")
                return
            elif len(found_devices) > 1:
                print(f"There is more than one device with the name '{name}'. You need to specify its UUID.")
                return
            device: Device = found_devices[0]

        game.login_stack.append(device)
    else:
        print("usage: device list|create|connect")


@command(["hostname"], CTX_DEVICE, "Show or modify the name of the device")
def handle_hostname(game: Game, _, args: List[str]):
    if args:
        name: str = " ".join(args)
        if not name:
            print("The name must not be empty.")
            return
        if len(name) > 15:
            print("The name cannot be longer than 15 characters.")
            return
        game.client.change_device_name(game.get_device().uuid, name)
    else:
        print(game.get_device().name)
