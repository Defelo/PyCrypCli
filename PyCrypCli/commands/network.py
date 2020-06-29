from typing import List, Optional

from PyCrypCli.commands.device import get_device

from PyCrypCli.commands.command import command
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


def handle_membership_request(context: DeviceContext, args: List[str], accept: bool):
    if len(args) not in (1, 2):
        print(f"usage: network {['deny', 'accept'][accept]} <network> [<device>]")
        return

    network: Optional[Network] = get_network(context, args[0])
    if network is None:
        print("This network does not exist.")
        return

    if len(args) == 1:
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

        device: Optional[Device] = get_device(context, args[1], devices)
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

    if accept:
        context.get_client().accept_network_membership_request(invitation.uuid)
    else:
        context.get_client().deny_network_membership_request(invitation.uuid)


@command("network", [DeviceContext])
def handle_network(context: DeviceContext, args: List[str]):
    """
    Manage your networks
    """

    if args:
        print("Unknown subcommand.")
    else:
        print_help(context, handle_network)


@handle_network.subcommand("list")
def handle_network_list(context: DeviceContext, _):
    """
    View the networks this device is a member of
    """

    networks: List[Network] = context.get_client().get_networks(context.host.uuid)

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

    networks: List[Network] = context.get_client().get_public_networks()

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
        print("usage: network create <name> public|private")
        return

    try:
        context.get_client().create_network(context.host.uuid, args[0], args[1] == "private")
    except MaximumNetworksReachedException:
        print("You already own two networks.")
    except InvalidNameException:
        print("Invalid name.")
    except NameAlreadyInUseException:
        print("This name is already in use.")


@handle_network.subcommand("members")
def handle_network_members(context: DeviceContext, args: List[str]):
    """
    View the members of one of your networks
    """

    if len(args) != 1:
        print("usage: network members <network>")
        return

    network: Optional[Network] = get_network(context, args[0])
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


@handle_network.subcommand("request")
def handle_network_request(context: DeviceContext, args: List[str]):
    """
    Request membership of a network
    """

    if len(args) != 1:
        print("usage: network request <network>")
        return

    network: Optional[Network] = get_network(context, args[0])
    if network is None:
        print("This network does not exist.")
        return

    try:
        context.get_client().request_network_membership(network.uuid, context.host.uuid)
    except AlreadyMemberOfNetworkException:
        print("This device is already a member of the network.")
    except InvitationAlreadyExistsException:
        print("You already requested to join this network.")


@handle_network.subcommand("requests")
def handle_network_requests(context: DeviceContext, args: List[str]):
    """
    View open membership requests of one of your networks
    """

    if len(args) != 1:
        print("usage: network requests <network>")
        return

    network: Optional[Network] = get_network(context, args[0])
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
        print(f"usage: network invite <network> <device>")
        return

    network: Optional[Network] = get_network(context, args[0])
    if network is None:
        print("This network does not exist.")
        return

    device: Optional[Device] = get_device(context, args[1])
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


@handle_network.subcommand("invitations")
def handle_network_invitations(context: DeviceContext, _):
    """
    View invitations for this device to other networks
    """

    invitations: List[NetworkInvitation] = context.get_client().get_network_invitations(context.host.uuid)
    if not invitations:
        print("There are no pending network invitations for this device.")
    else:
        print("Pending network invitations:")
    for invitation in invitations:
        network: Network = context.get_client().get_network_by_uuid(invitation.network)
        owner: str = " (owner)" * (network.owner == context.host.uuid)
        print(f" - [{['public', 'private'][network.hidden]}] {network.name}{owner} (UUID: {network.uuid})")


@handle_network.subcommand("leave")
def handle_network_leave(context: DeviceContext, args: List[str]):
    """
    Leave a network
    """

    if len(args) != 1:
        print("usage: network leave <network>")
        return

    network: Optional[Network] = get_network(context, args[0])
    if network is None:
        print("This network does not exist.")
        return

    try:
        context.get_client().leave_network(context.host.uuid, network.uuid)
    except CannotLeaveOwnNetworkException:
        print("You cannot leave your own network.")


@handle_network.subcommand("kick")
def handle_network_kick(context: DeviceContext, args: List[str]):
    """
    Kick a device from one of your networks
    """

    if len(args) != 2:
        print(f"usage: network kick <network> <device>")
        return

    network: Optional[Network] = get_network(context, args[0])
    if network is None:
        print("This network does not exist.")
        return

    devices: List[Device] = []
    for member in context.get_client().get_members_of_network(network.uuid):
        devices.append(context.get_client().device_info(member.device))

    device: Optional[Device] = get_device(context, args[1], devices)
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


@handle_network.subcommand("delete")
def handle_network_delete(context: DeviceContext, args: List[str]):
    """
    Delete one of your networks
    """

    if len(args) != 1:
        print("usage: network delete <network>")
        return

    network: Optional[Network] = get_network(context, args[0])
    if network is None:
        print("This network does not exist.")
        return

    try:
        context.get_client().delete_network(network.uuid)
    except NetworkNotFoundException:
        print("Permission denied.")


@handle_network_members.completer()
@handle_network_request.completer()
@handle_network_requests.completer()
@handle_network_leave.completer()
@handle_network_delete.completer()
def network_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return list(
            # networks of this device
            {network.name for network in context.get_client().get_networks(context.host.uuid)}
            # public networks
            | {network.name for network in context.get_client().get_public_networks()}
            # networks from incoming invitations
            | {
                context.get_client().get_network_by_uuid(invitation.network).name
                for invitation in context.get_client().get_network_invitations(context.host.uuid)
            }
        )


@handle_network_create.completer()
def network_create_completer(_, args: List[str]) -> List[str]:
    if len(args) == 2:
        return ["public", "private"]


@handle_network_accept.completer()
@handle_network_deny.completer()
def network_accept_deny_completer(context: DeviceContext, args: List[str]) -> List[str]:
    if len(args) == 1:
        return list(
            {network.name for network in context.get_client().get_networks(context.host.uuid)}
            | {
                context.get_client().get_network_by_uuid(invitation.network).name
                for invitation in context.get_client().get_network_invitations(context.host.uuid)
            }
        )
    elif len(args) == 2:
        network: Optional[Network] = get_network(context, args[0])
        if network is None:
            return []
        device_names: List[str] = []
        for request in context.get_client().get_network_membership_requests(network.uuid):
            device: Optional[Device] = context.get_client().device_info(request.device)
            if device is not None:
                device_names.append(device.name)
        return [name for name in device_names if device_names.count(name) == 1]


@handle_network_invite.completer()
def network_invite_completer(context: DeviceContext, args: List[str]):
    if len(args) == 1:
        return list({network.name for network in context.get_client().get_networks(context.host.uuid)})
    elif len(args) == 2:
        device_names: List[str] = [device.name for device in context.get_client().get_devices()]
        return [name for name in device_names if device_names.count(name) == 1]


@handle_network_kick.completer()
def network_kick_completer(context: DeviceContext, args: List[str]):
    if len(args) == 1:
        return list({network.name for network in context.get_client().get_networks(context.host.uuid)})
    elif len(args) == 2:
        network: Optional[Network] = get_network(context, args[0])
        if network is None:
            return []
        device_names: List[str] = []
        for member in context.get_client().get_members_of_network(network.uuid):
            device_names.append(context.get_client().device_info(member.device).name)
        return [name for name in device_names if device_names.count(name) == 1]
