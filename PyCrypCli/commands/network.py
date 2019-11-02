from typing import List, Optional

from PyCrypCli.commands.device import get_device

from PyCrypCli.commands.command import command, completer
from PyCrypCli.context import DeviceContext
from PyCrypCli.exceptions import (
    MaximumNetworksReachedException,
    InvalidNameException,
    NameAlreadyInUseException,
    NetworkNotFoundException,
    AlreadyMemberOfNetworkException,
    InvitationAlreadyExistsException,
    NoPermissionsException,
    CannotLeaveOwnNetworkException,
    CannotKickOwnerException,
)
from PyCrypCli.game_objects import Network, NetworkMembership, Device, NetworkInvitation
from PyCrypCli.util import is_uuid


def get_network(context: DeviceContext, name_or_uuid: str) -> Optional[Network]:
    if is_uuid(name_or_uuid):
        try:
            return context.get_client().get_network_by_uuid(name_or_uuid)
        except NetworkNotFoundException:
            pass

    try:
        return context.get_client().get_network_by_name(name_or_uuid)
    except NetworkNotFoundException:
        pass


@command(["network"], [DeviceContext], "Manage your networks")
def handle_network(context: DeviceContext, args: List[str]):
    subcommands = [
        "list",
        "public",
        "create",
        "members",
        "request",
        "requests",
        "invite",
        "invitations",
        "accept",
        "deny",
        "leave",
        "kick",
        "delete",
    ]
    if not args:
        print("usage: network " + "|".join(subcommands))
        return

    if args[0] == "list":
        networks: List[Network] = context.get_client().get_networks(context.host.uuid)

        if not networks:
            print("This device is not a member of any network.")
        else:
            print("Networks this device is a member of:")
        for network in networks:
            owner: str = " (owner)" * (network.owner == context.host.uuid)
            print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")
    elif args[0] == "public":
        networks: List[Network] = context.get_client().get_public_networks()

        if not networks:
            print("There is no public network.")
        else:
            print("Public networks:")
        for network in networks:
            owner: str = " (owner)" * (network.owner == context.host.uuid)
            print(f" - {network.name}{owner} (UUID: {network.uuid})")
    elif args[0] == "create":
        if len(args) != 3 or args[2] not in ("public", "private"):
            print("usage: network create <name> public|private")
            return

        try:
            context.get_client().create_network(context.host.uuid, args[1], args[2] == "private")
        except MaximumNetworksReachedException:
            print("You already own two networks.")
        except InvalidNameException:
            print("Invalid name.")
        except NameAlreadyInUseException:
            print("This name is already in use.")
    elif args[0] == "members":
        if len(args) != 2:
            print("usage: network members <network>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        try:
            members: List[NetworkMembership] = context.get_client().get_members_of_network(network.uuid)
        except NetworkNotFoundException:
            print("Permission denied.")
            return

        if not members:
            print("This network has no members.")
        else:
            print(f"Members of '{network.name}':")
        for member in members:
            device: Device = context.get_client().device_info(member.device)
            print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")
    elif args[0] == "request":
        if len(args) != 2:
            print("usage: network request <network>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        try:
            context.get_client().request_network_membership(network.uuid, context.host.uuid)
        except AlreadyMemberOfNetworkException:
            print("This device is already a member of the network.")
        except InvitationAlreadyExistsException:
            print("You already requested to join this network.")
    elif args[0] == "requests":
        if len(args) != 2:
            print("usage: network requests <network>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        try:
            requests: List[NetworkInvitation] = context.get_client().get_network_membership_requests(network.uuid)
        except NoPermissionsException:
            print("Permission denied.")
            return

        if not requests:
            print("There are no pending requests for this network.")
        else:
            print("Pending requests:")
        for request in requests:
            device: Device = context.get_client().device_info(request.device)
            print(f" - {device.name} (UUID: {device.uuid})")
    elif args[0] in ("accept", "deny"):
        if len(args) < 2:
            print(f"usage: network {args[0]} <network> [<device>]")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        if len(args) == 2:
            for invitation in context.get_client().get_network_invitations(context.host.uuid):
                if invitation.network == network.uuid:
                    break
            else:
                print("Invitation not found.")
                return
        else:
            devices: List[Device] = []
            for request in context.get_client().get_network_membership_requests(network.uuid):
                device: Optional[Device] = context.get_client().device_info(request.device)
                if device is not None:
                    devices.append(device)

            device: Optional[Device] = get_device(context, args[2], devices)
            if device is None:
                print("Device not found.")
                return

            try:
                for invitation in context.get_client().get_network_membership_requests(network.uuid):
                    if invitation.network == network.uuid and invitation.device == device.uuid:
                        break
                else:
                    print("Join request not found.")
                    return
            except NoPermissionsException:
                print("Permission denied.")
                return

        if args[0] == "accept":
            context.get_client().accept_network_membership_request(invitation.uuid)
        else:
            context.get_client().deny_network_membership_request(invitation.uuid)
    elif args[0] == "invite":
        if len(args) != 3:
            print(f"usage: network invite <network> <device>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        device: Optional[Device] = get_device(context, args[2])
        if device is None:
            print("Device not found.")
            return

        try:
            context.get_client().invite_to_network(device.uuid, network.uuid)
        except NetworkNotFoundException:
            print("Permission denied.")
        except AlreadyMemberOfNetworkException:
            print("Device is already a member of this network.")
        except InvitationAlreadyExistsException:
            print("An invitation for this device already exists.")
    elif args[0] == "invitations":
        invitations: List[NetworkInvitation] = context.get_client().get_network_invitations(context.host.uuid)
        if not invitations:
            print("There are no pending network invitations for this device.")
        else:
            print("Pending network invitations:")
        for invitation in invitations:
            network: Network = context.get_client().get_network_by_uuid(invitation.network)
            owner: str = " (owner)" * (network.owner == context.host.uuid)
            print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")
    elif args[0] == "leave":
        if len(args) != 2:
            print("usage: network leave <network>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        try:
            context.get_client().leave_network(context.host.uuid, network.uuid)
        except CannotLeaveOwnNetworkException:
            print("You cannot leave your own network.")
    elif args[0] == "kick":
        if len(args) != 3:
            print(f"usage: network kick <network> <device>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        devices: List[Device] = []
        for member in context.get_client().get_members_of_network(network.uuid):
            devices.append(context.get_client().device_info(member.device))

        device: Optional[Device] = get_device(context, args[2], devices)
        if device is None:
            print("Device not found.")
            return

        try:
            context.get_client().kick_from_network(device.uuid, network.uuid)
        except NetworkNotFoundException:
            print("Permission denied.")
        except NoPermissionsException:
            print("Permission denied.")
        except CannotKickOwnerException:
            print("You cannot kick the owner of the network.")
    elif args[0] == "delete":
        if len(args) != 2:
            print("usage: network delete <network>")
            return

        network: Optional[Network] = get_network(context, args[1])
        if network is None:
            print("This network does not exist.")
            return

        try:
            context.get_client().delete_network(network.uuid)
        except NetworkNotFoundException:
            print("Permission denied.")
    else:
        print("usage: network " + "|".join(subcommands))


@completer([handle_network])
def network_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return [
            "list",
            "public",
            "create",
            "members",
            "request",
            "requests",
            "invite",
            "invitations",
            "accept",
            "deny",
            "leave",
            "kick",
            "delete",
        ]
    elif len(args) == 2:
        if args[0] in ("members", "request", "requests", "invite", "accept", "deny", "leave", "kick", "delete"):
            return list(
                {network.name for network in context.get_client().get_networks(context.host.uuid)}
                | {network.name for network in context.get_client().get_public_networks()}
                | {
                    context.get_client().get_network_by_uuid(invitation.network).name
                    for invitation in context.get_client().get_network_invitations(context.host.uuid)
                }
            )
    elif len(args) == 3:
        if args[0] == "create":
            return ["public", "private"]
        elif args[0] in ("accept", "deny"):
            network: Optional[Network] = get_network(context, args[1])
            if network is None:
                return []
            device_names: List[str] = []
            for request in context.get_client().get_network_membership_requests(network.uuid):
                device: Optional[Device] = context.get_client().device_info(request.device)
                if device is not None:
                    device_names.append(device.name)
            return [name for name in device_names if device_names.count(name) == 1]
        elif args[0] == "invite":
            device_names: List[str] = [device.name for device in context.get_client().get_devices()]
            return [name for name in device_names if device_names.count(name) == 1]
        elif args[0] == "kick":
            network: Optional[Network] = get_network(context, args[1])
            if network is None:
                return []
            device_names: List[str] = []
            for member in context.get_client().get_members_of_network(network.uuid):
                device_names.append(context.get_client().device_info(member.device).name)
            return [name for name in device_names if device_names.count(name) == 1]
