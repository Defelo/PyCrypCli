from typing import Any

from .command import command, CommandError
from .device import get_device
from .help import print_help
from ..context import DeviceContext
from ..exceptions import (
    MaximumNetworksReachedError,
    InvalidNameError,
    NameAlreadyInUseError,
    NetworkNotFoundError,
    AlreadyMemberOfNetworkError,
    InvitationAlreadyExistsError,
    NoPermissionsError,
    CannotLeaveOwnNetworkError,
    CannotKickOwnerError,
    DeviceNotFoundError,
)
from ..models import Network, NetworkMembership, Device, NetworkInvitation
from ..util import is_uuid


def get_network(context: DeviceContext, name_or_uuid: str) -> Network:
    if is_uuid(name_or_uuid):
        try:
            return Network.get_by_uuid(context.client, name_or_uuid)
        except NetworkNotFoundError:
            pass

    try:
        return Network.get_network_by_name(context.client, name_or_uuid)
    except NetworkNotFoundError:
        raise CommandError("This network does not exist.")


def handle_membership_request(context: DeviceContext, args: list[str], accept: bool) -> None:
    if len(args) not in (1, 2):
        raise CommandError(f"usage: network {['deny', 'accept'][accept]} <network> [<device>]")

    network: Network = get_network(context, args[0])

    if len(args) == 1:
        for invitation in context.host.get_network_invitations():
            if invitation.network_uuid == network.uuid:
                break
        else:
            raise CommandError("Invitation not found.")
    else:
        devices: list[Device] = []
        for request in network.get_membership_requests():
            try:
                devices.append(Device.get_device(context.client, request.device_uuid))
            except DeviceNotFoundError:
                pass

        device: Device = get_device(context, args[1], devices)
        try:
            for invitation in network.get_membership_requests():
                if invitation.network_uuid == network.uuid and invitation.device_uuid == device.uuid:
                    break
            else:
                raise CommandError("Join request not found.")
        except NoPermissionsError:
            raise CommandError("Permission denied.")

    if accept:
        invitation.accept()
    else:
        invitation.deny()


@command("network", [DeviceContext])
def handle_network(context: DeviceContext, args: list[str]) -> None:
    """
    Manage your networks
    """

    if args:
        raise CommandError("Unknown subcommand.")
    print_help(context, handle_network)


@handle_network.subcommand("list")
def handle_network_list(context: DeviceContext, _: Any) -> None:
    """
    View the networks this device is a member of
    """

    networks: list[Network] = context.host.get_networks()

    if not networks:
        print("This device is not a member of any network.")
    else:
        print("Networks this device is a member of:")
    for network in networks:
        owner: str = " (owner)" * (network.owner_uuid == context.host.uuid)
        print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("public")
def handle_network_public(context: DeviceContext, _: Any) -> None:
    """
    View public networks
    """

    networks: list[Network] = Network.get_public_networks(context.client)

    if not networks:
        print("There is no public network.")
    else:
        print("Public networks:")
    for network in networks:
        owner: str = " (owner)" * (network.owner_uuid == context.host.uuid)
        print(f" - {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("create")
def handle_network_create(context: DeviceContext, args: list[str]) -> None:
    """
    Create a new network
    """

    if len(args) != 2 or args[1] not in ("public", "private"):
        raise CommandError("usage: network create <name> public|private")

    try:
        context.host.create_network(args[0], args[1] == "private")
    except MaximumNetworksReachedError:
        raise CommandError("You already own two networks.")
    except InvalidNameError:
        raise CommandError("Invalid name.")
    except NameAlreadyInUseError:
        raise CommandError("This name is already in use.")


@handle_network.subcommand("members")
def handle_network_members(context: DeviceContext, args: list[str]) -> None:
    """
    View the members of one of your networks
    """

    if len(args) != 1:
        raise CommandError("usage: network members <network>")

    network: Network = get_network(context, args[0])

    try:
        members: list[NetworkMembership] = network.get_members()
    except NetworkNotFoundError:
        raise CommandError("Permission denied.")

    if not members:
        print("This network has no members.")
    else:
        print(f"Members of '{network.name}':")
    for member in members:
        device: Device = Device.get_device(context.client, member.device_uuid)
        print(f" - [{['off', 'on'][device.powered_on]}] {device.name} (UUID: {device.uuid})")


@handle_network.subcommand("request")
def handle_network_request(context: DeviceContext, args: list[str]) -> None:
    """
    Request membership of a network
    """

    if len(args) != 1:
        raise CommandError("usage: network request <network>")

    network: Network = get_network(context, args[0])

    try:
        network.request_membership(context.host)
    except AlreadyMemberOfNetworkError:
        raise CommandError("This device is already a member of the network.")
    except InvitationAlreadyExistsError:
        raise CommandError("You already requested to join this network.")


@handle_network.subcommand("requests")
def handle_network_requests(context: DeviceContext, args: list[str]) -> None:
    """
    View open membership requests of one of your networks
    """

    if len(args) != 1:
        raise CommandError("usage: network requests <network>")

    network: Network = get_network(context, args[0])

    try:
        requests: list[NetworkInvitation] = network.get_membership_requests()
    except NoPermissionsError:
        raise CommandError("Permission denied.")

    if not requests:
        print("There are no pending requests for this network.")
    else:
        print("Pending requests:")
    for request in requests:
        device: Device = Device.get_device(context.client, request.device_uuid)
        print(f" - {device.name} (UUID: {device.uuid})")


@handle_network.subcommand("accept")
def handle_network_accept(context: DeviceContext, args: list[str]) -> None:
    """
    Accept a membership request or an invitation
    """

    handle_membership_request(context, args, True)


@handle_network.subcommand("deny")
def handle_network_deny(context: DeviceContext, args: list[str]) -> None:
    """
    Deny a membership request or an invitation
    """

    handle_membership_request(context, args, False)


@handle_network.subcommand("invite")
def handle_network_invite(context: DeviceContext, args: list[str]) -> None:
    """
    Invite a device to one of your networks
    """

    if len(args) != 2:
        raise CommandError("usage: network invite <network> <device>")

    network: Network = get_network(context, args[0])

    device: Device = get_device(context, args[1])
    try:
        network.invite_device(device)
    except NetworkNotFoundError:
        raise CommandError("Permission denied.")
    except AlreadyMemberOfNetworkError:
        raise CommandError("Device is already a member of this network.")
    except InvitationAlreadyExistsError:
        raise CommandError("An invitation for this device already exists.")


@handle_network.subcommand("invitations")
def handle_network_invitations(context: DeviceContext, _: Any) -> None:
    """
    View invitations for this device to other networks
    """

    invitations: list[NetworkInvitation] = context.host.get_network_invitations()
    if not invitations:
        print("There are no pending network invitations for this device.")
    else:
        print("Pending network invitations:")
    for invitation in invitations:
        network: Network = Network.get_by_uuid(context.client, invitation.network_uuid)
        owner: str = " (owner)" * (network.owner_uuid == context.host.uuid)
        print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("leave")
def handle_network_leave(context: DeviceContext, args: list[str]) -> None:
    """
    Leave a network
    """

    if len(args) != 1:
        raise CommandError("usage: network leave <network>")

    network: Network = get_network(context, args[0])

    try:
        network.leave(context.host)
    except CannotLeaveOwnNetworkError:
        raise CommandError("You cannot leave your own network.")


@handle_network.subcommand("kick")
def handle_network_kick(context: DeviceContext, args: list[str]) -> None:
    """
    Kick a device from one of your networks
    """

    if len(args) != 2:
        raise CommandError("usage: network kick <network> <device>")

    network: Network = get_network(context, args[0])

    devices: list[Device] = []
    for member in network.get_members():
        devices.append(Device.get_device(context.client, member.device_uuid))

    device: Device = get_device(context, args[1], devices)
    try:
        network.kick(device)
    except NetworkNotFoundError:
        raise CommandError("Permission denied.")
    except NoPermissionsError:
        raise CommandError("Permission denied.")
    except CannotKickOwnerError:
        raise CommandError("You cannot kick the owner of the network.")


@handle_network.subcommand("delete")
def handle_network_delete(context: DeviceContext, args: list[str]) -> None:
    """
    Delete one of your networks
    """

    if len(args) != 1:
        raise CommandError("usage: network delete <network>")

    network: Network = get_network(context, args[0])

    try:
        network.delete()
    except NetworkNotFoundError:
        raise CommandError("Permission denied.")


def device_network_names(context: DeviceContext) -> list[str]:
    return [network.name for network in context.host.get_networks()]


def public_network_names(context: DeviceContext) -> list[str]:
    return [network.name for network in Network.get_public_networks(context.client)]


def invitation_network_names(context: DeviceContext) -> list[str]:
    return [
        Network.get_by_uuid(context.client, invitation.network_uuid).name
        for invitation in context.host.get_network_invitations()
    ]


@handle_network_members.completer()
@handle_network_request.completer()
@handle_network_requests.completer()
@handle_network_leave.completer()
@handle_network_delete.completer()
def network_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return [*{*device_network_names(context), *public_network_names(context), *invitation_network_names(context)}]
    return []


@handle_network_create.completer()
def network_create_completer(_: Any, args: list[str]) -> list[str]:
    if len(args) == 2:
        return ["public", "private"]
    return []


@handle_network_accept.completer()
@handle_network_deny.completer()
def network_accept_deny_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return [*{*device_network_names(context), *invitation_network_names(context)}]
    if len(args) == 2:
        try:
            network: Network = get_network(context, args[0])
        except CommandError:
            return []
        device_names: list[str] = []
        for request in network.get_membership_requests():
            try:
                device_names.append(Device.get_device(context.client, request.device_uuid).name)
            except DeviceNotFoundError:
                pass
        return [name for name in device_names if device_names.count(name) == 1]
    return []


@handle_network_invite.completer()
def network_invite_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return [*{*device_network_names(context)}]
    if len(args) == 2:
        device_names: list[str] = [device.name for device in Device.list_devices(context.client)]
        return [name for name in device_names if device_names.count(name) == 1]
    return []


@handle_network_kick.completer()
def network_kick_completer(context: DeviceContext, args: list[str]) -> list[str]:
    if len(args) == 1:
        return [*{*device_network_names(context)}]
    if len(args) == 2:
        try:
            network: Network = get_network(context, args[0])
        except CommandError:
            return []
        device_names: list[str] = []
        for member in network.get_members():
            device_names.append(Device.get_device(context.client, member.device_uuid).name)
        return [name for name in device_names if device_names.count(name) == 1]
    return []
