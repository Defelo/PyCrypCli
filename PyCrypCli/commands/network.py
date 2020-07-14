from typing import List

from PyCrypCli.commands import command, CommandError
from PyCrypCli.commands.device import get_device
from PyCrypCli.commands.help import print_help
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
    DeviceNotFoundException,
)
from PyCrypCli.game_objects import Network, NetworkMembership, Device, NetworkInvitation
from PyCrypCli.util import is_uuid


def get_network(context: DeviceContext, name_or_uuid: str) -> Network:
    if is_uuid(name_or_uuid):
        try:
            return Network.get_by_uuid(context.client, name_or_uuid)
        except NetworkNotFoundException:
            pass

    try:
        return Network.get_network_by_name(context.client, name_or_uuid)
    except NetworkNotFoundException:
        raise CommandError("This network does not exist.")


def handle_membership_request(context: DeviceContext, args: List[str], accept: bool):
    if len(args) not in (1, 2):
        raise CommandError(f"usage: network {['deny', 'accept'][accept]} <network> [<device>]")

    network: Network = get_network(context, args[0])

    if len(args) == 1:
        for invitation in context.host.get_network_invitations():
            if invitation.network == network.uuid:
                break
        else:
            raise CommandError("Invitation not found.")
    else:
        devices: List[Device] = []
        for request in network.get_membership_requests():
            try:
                devices.append(Device.get_device(context.client, request.device))
            except DeviceNotFoundException:
                pass

        device: Device = get_device(context, args[1], devices)
        try:
            for invitation in network.get_membership_requests():
                if invitation.network == network.uuid and invitation.device == device.uuid:
                    break
            else:
                raise CommandError("Join request not found.")
        except NoPermissionsException:
            raise CommandError("Permission denied.")

    if accept:
        invitation.accept()
    else:
        invitation.deny()


@command("network", [DeviceContext])
def handle_network(context: DeviceContext, args: List[str]):
    """
    Manage your networks
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_network)


@handle_network.subcommand("list")
def handle_network_list(context: DeviceContext, _):
    """
    View the networks this device is a member of
    """

    networks: List[Network] = context.host.get_networks()

    if not networks:
        print("This device is not a member of any network.")
    else:
        print("Networks this device is a member of:")
    for network in networks:
        owner: str = " (owner)" * (network.owner == context.host.uuid)
        print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("public")
def handle_network_public(context: DeviceContext, _):
    """
    View public networks
    """

    networks: List[Network] = Network.get_public_networks(context.client)

    if not networks:
        print("There is no public network.")
    else:
        print("Public networks:")
    for network in networks:
        owner: str = " (owner)" * (network.owner == context.host.uuid)
        print(f" - {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("create")
def handle_network_create(context: DeviceContext, args: List[str]):
    """
    Create a new network
    """

    if len(args) != 2 or args[1] not in ("public", "private"):
        raise CommandError("usage: network create <name> public|private")

    try:
        context.host.create_network(args[0], args[1] == "private")
    except MaximumNetworksReachedException:
        raise CommandError("You already own two networks.")
    except InvalidNameException:
        raise CommandError("Invalid name.")
    except NameAlreadyInUseException:
        raise CommandError("This name is already in use.")


@handle_network.subcommand("members")
def handle_network_members(context: DeviceContext, args: List[str]):
    """
    View the members of one of your networks
    """

    if len(args) != 1:
        raise CommandError("usage: network members <network>")

    network: Network = get_network(context, args[0])

    try:
        members: List[NetworkMembership] = network.get_members()
    except NetworkNotFoundException:
        raise CommandError("Permission denied.")

    if not members:
        print("This network has no members.")
    else:
        print(f"Members of '{network.name}':")
    for member in members:
        device: Device = Device.get_device(context.client, member.device)
        print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")


@handle_network.subcommand("request")
def handle_network_request(context: DeviceContext, args: List[str]):
    """
    Request membership of a network
    """

    if len(args) != 1:
        raise CommandError("usage: network request <network>")

    network: Network = get_network(context, args[0])

    try:
        network.request_membership(context.host)
    except AlreadyMemberOfNetworkException:
        raise CommandError("This device is already a member of the network.")
    except InvitationAlreadyExistsException:
        raise CommandError("You already requested to join this network.")


@handle_network.subcommand("requests")
def handle_network_requests(context: DeviceContext, args: List[str]):
    """
    View open membership requests of one of your networks
    """

    if len(args) != 1:
        raise CommandError("usage: network requests <network>")

    network: Network = get_network(context, args[0])

    try:
        requests: List[NetworkInvitation] = network.get_membership_requests()
    except NoPermissionsException:
        raise CommandError("Permission denied.")

    if not requests:
        print("There are no pending requests for this network.")
    else:
        print("Pending requests:")
    for request in requests:
        device: Device = Device.get_device(context.client, request.device)
        print(f" - {device.name} (UUID: {device.uuid})")


@handle_network.subcommand("accept")
def handle_network_accept(context: DeviceContext, args: List[str]):
    """
    Accept a membership request or an invitation
    """

    handle_membership_request(context, args, True)


@handle_network.subcommand("deny")
def handle_network_deny(context: DeviceContext, args: List[str]):
    """
    Deny a membership request or an invitation
    """

    handle_membership_request(context, args, False)


@handle_network.subcommand("invite")
def handle_network_invite(context: DeviceContext, args: List[str]):
    """
    Invite a device to one of your networks
    """

    if len(args) != 2:
        raise CommandError("usage: network invite <network> <device>")

    network: Network = get_network(context, args[0])

    device: Device = get_device(context, args[1])
    try:
        network.invite_device(device)
    except NetworkNotFoundException:
        raise CommandError("Permission denied.")
    except AlreadyMemberOfNetworkException:
        raise CommandError("Device is already a member of this network.")
    except InvitationAlreadyExistsException:
        raise CommandError("An invitation for this device already exists.")


@handle_network.subcommand("invitations")
def handle_network_invitations(context: DeviceContext, _):
    """
    View invitations for this device to other networks
    """

    invitations: List[NetworkInvitation] = context.host.get_network_invitations()
    if not invitations:
        print("There are no pending network invitations for this device.")
    else:
        print("Pending network invitations:")
    for invitation in invitations:
        network: Network = Network.get_by_uuid(context.client, invitation.network)
        owner: str = " (owner)" * (network.owner == context.host.uuid)
        print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("leave")
def handle_network_leave(context: DeviceContext, args: List[str]):
    """
    Leave a network
    """

    if len(args) != 1:
        raise CommandError("usage: network leave <network>")

    network: Network = get_network(context, args[0])

    try:
        network.leave(context.host)
    except CannotLeaveOwnNetworkException:
        raise CommandError("You cannot leave your own network.")


@handle_network.subcommand("kick")
def handle_network_kick(context: DeviceContext, args: List[str]):
    """
    Kick a device from one of your networks
    """

    if len(args) != 2:
        raise CommandError("usage: network kick <network> <device>")

    network: Network = get_network(context, args[0])

    devices: List[Device] = []
    for member in network.get_members():
        devices.append(Device.get_device(context.client, member.device))

    device: Device = get_device(context, args[1], devices)
    try:
        network.kick(device)
    except NetworkNotFoundException:
        raise CommandError("Permission denied.")
    except NoPermissionsException:
        raise CommandError("Permission denied.")
    except CannotKickOwnerException:
        raise CommandError("You cannot kick the owner of the network.")


@handle_network.subcommand("delete")
def handle_network_delete(context: DeviceContext, args: List[str]):
    """
    Delete one of your networks
    """

    if len(args) != 1:
        raise CommandError("usage: network delete <network>")

    network: Network = get_network(context, args[0])

    try:
        network.delete()
    except NetworkNotFoundException:
        raise CommandError("Permission denied.")


def device_network_names(context: DeviceContext) -> List[str]:
    return [network.name for network in context.host.get_networks()]


def public_network_names(context: DeviceContext) -> List[str]:
    return [network.name for network in Network.get_public_networks(context.client)]


def invitation_network_names(context: DeviceContext) -> List[str]:
    return [
        Network.get_by_uuid(context.client, invitation.network).name
        for invitation in context.host.get_network_invitations()
    ]


@handle_network_members.completer()
@handle_network_request.completer()
@handle_network_requests.completer()
@handle_network_leave.completer()
@handle_network_delete.completer()
def network_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return [*{*device_network_names(context), *public_network_names(context), *invitation_network_names(context)}]
    return []


@handle_network_create.completer()
def network_create_completer(_, args: List[str]) -> List[str]:
    if len(args) == 2:
        return ["public", "private"]
    return []


@handle_network_accept.completer()
@handle_network_deny.completer()
def network_accept_deny_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return [*{*device_network_names(context), *invitation_network_names(context)}]
    if len(args) == 2:
        try:
            network: Network = get_network(context, args[0])
        except CommandError:
            return []
        device_names: List[str] = []
        for request in network.get_membership_requests():
            try:
                device_names.append(Device.get_device(context.client, request.device).name)
            except DeviceNotFoundException:
                pass
        return [name for name in device_names if device_names.count(name) == 1]
    return []


@handle_network_invite.completer()
def network_invite_completer(context: DeviceContext, args: List[str]):
    if len(args) == 1:
        return [*{*device_network_names(context)}]
    if len(args) == 2:
        device_names: List[str] = [device.name for device in Device.list_devices(context.client)]
        return [name for name in device_names if device_names.count(name) == 1]
    return []


@handle_network_kick.completer()
def network_kick_completer(context: DeviceContext, args: List[str]):
    if len(args) == 1:
        return [*{*device_network_names(context)}]
    if len(args) == 2:
        try:
            network: Network = get_network(context, args[0])
        except CommandError:
            return []
        device_names: List[str] = []
        for member in network.get_members():
            device_names.append(Device.get_device(context.client, member.device).name)
        return [name for name in device_names if device_names.count(name) == 1]
    return []
