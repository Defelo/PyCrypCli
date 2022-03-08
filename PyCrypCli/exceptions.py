import json
from typing import Any


class ClientNotReadyError(Exception):
    pass


class InvalidServerURLError(Exception):
    pass


class CommandRegistrationError(Exception):
    def __init__(self, name: str, subcommand: bool = False):
        super().__init__(f"The {'sub' * subcommand}command {name} has already been registered.")


class NoDocStringError(Exception):
    def __init__(self, name: str, subcommand: bool = False):
        super().__init__(f"The {'sub' * subcommand}command {name} is missing a docstring.")


class LoggedInError(Exception):
    def __init__(self) -> None:
        super().__init__("Endpoint cannot be used while client is logged in.")


class LoggedOutError(Exception):
    def __init__(self) -> None:
        super().__init__("Endpoint can only be used while client is logged in.")


class InvalidServerResponseError(Exception):
    def __init__(self, response: dict[Any, Any]):
        super().__init__("Invalid Server Response: " + json.dumps(response))


class InvalidSessionTokenError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid session token")


class WeakPasswordError(Exception):
    def __init__(self) -> None:
        super().__init__("Password is too weak")


class UsernameAlreadyExistsError(Exception):
    def __init__(self) -> None:
        super().__init__("Username already exists")


class InvalidLoginError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid Login Credentials")


class InvalidWalletFileError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid wallet file")


class UnknownMicroserviceError(Exception):
    def __init__(self, ms: str):
        super().__init__("Unknown Microservice: " + ms)


class MicroserviceException(Exception):
    error: str | None = None

    def __init__(self, error: str | None = None, args: list[Any] | None = None):
        super().__init__(error or "")
        self.error = error
        self.params = args


class InternalError(MicroserviceException):
    error: str = "internal error"


class NoResponseTimeoutError(MicroserviceException):
    error: str = "no response - timeout"


class InvalidRequestError(MicroserviceException):
    error: str = "invalid_request"


class AlreadyOwnADeviceError(MicroserviceException):
    error: str = "already_own_a_device"


class PermissionDeniedError(MicroserviceException):
    error: str = "permission_denied"


class DeviceNotFoundError(MicroserviceException):
    error: str = "device_not_found"


class DevicePoweredOffError(MicroserviceException):
    error: str = "device_powered_off"


class DeviceNotOnlineError(MicroserviceException):
    error: str = "device_not_online"


class DeviceIsStarterDeviceError(MicroserviceException):
    error: str = "device_is_starter_device"


class MaximumDevicesReachedError(MicroserviceException):
    error: str = "maximum_devices_reached"


class ElementPartNotFoundError(MicroserviceException):
    error: str = "element_(.+)_not_found"


class PartNotInInventoryError(MicroserviceException):
    error: str = "(.+)_not_in_inventory"


class MissingPartError(MicroserviceException):
    error: str = "missing_(.+)"


class IncompatibleCPUSocketError(MicroserviceException):
    error: str = "incompatible_cpu_socket"


class NotEnoughRAMSlotsError(MicroserviceException):
    error: str = "not_enough_ram_slots"


class IncompatibleRAMTypesError(MicroserviceException):
    error: str = "incompatible_ram_types"


class IncompatibleDriverInterfaceError(MicroserviceException):
    error: str = "incompatible_drive_interface"


class FileNotFoundError(MicroserviceException):
    error: str = "file_not_found"


class FileNotChangeableError(MicroserviceException):
    error: str = "file_not_changeable"


class FileAlreadyExistsError(MicroserviceException):
    error: str = "file_already_exists"


class ParentDirectoryNotFoundError(MicroserviceException):
    error: str = "parent_directory_not_found"


class CanNotMoveDirIntoItselfError(MicroserviceException):
    error: str = "can_not_move_dir_into_itself"


class DirectoriesCanNotBeUpdatedError(MicroserviceException):
    error: str = "directories_can_not_be_updated"


class DirectoryCanNotHaveTextContentError(MicroserviceException):
    error: str = "directory_can_not_have_textcontent"


class AlreadyOwnAWalletError(MicroserviceException):
    error: str = "already_own_a_wallet"


class UnknownSourceOrDestinationError(MicroserviceException):
    error: str = "unknown_source_or_destination"


class NotEnoughCoinsError(MicroserviceException):
    error: str = "not_enough_coins"


class AlreadyOwnThisServiceError(MicroserviceException):
    error: str = "already_own_this_service"


class ServiceNotSupportedError(MicroserviceException):
    error: str = "service_not_supported"


class ServiceNotRunningError(MicroserviceException):
    error: str = "service_not_running"


class CannotToggleDirectlyError(MicroserviceException):
    error: str = "cannot_toggle_directly"


class CouldNotStartServiceError(MicroserviceException):
    error: str = "could_not_start_service"


class WalletNotFoundError(MicroserviceException):
    error: str = "wallet_not_found"


class MinerNotFoundError(MicroserviceException):
    error: str = "miner_not_found"


class ServiceNotFoundError(MicroserviceException):
    error: str = "service_not_found"


class UnknownServiceError(MicroserviceException):
    error: str = "unknown_service"


class ServiceCannotBeUsedError(MicroserviceException):
    error: str = "service_cannot_be_used"


class CannotDeleteEnforcedServiceError(MicroserviceException):
    error: str = "cannot_delete_enforced_service"


class AttackNotRunningError(MicroserviceException):
    error: str = "attack_not_running"


class ItemNotFoundError(MicroserviceException):
    error: str = "item_not_found"


class CannotTradeWithYourselfError(MicroserviceException):
    error: str = "cannot_trade_with_yourself"


class UserUUIDDoesNotExistError(MicroserviceException):
    error: str = "user_uuid_does_not_exist"


class NetworkNotFoundError(MicroserviceException):
    error: str = "network_not_found"


class AlreadyMemberOfNetworkError(MicroserviceException):
    error: str = "already_member_of_network"


class InvitationAlreadyExistsError(MicroserviceException):
    error: str = "invitation_already_exists"


class CannotLeaveOwnNetworkError(MicroserviceException):
    error: str = "cannot_leave_own_network"


class CannotKickOwnerError(MicroserviceException):
    error: str = "cannot_kick_owner"


class MaximumNetworksReachedError(MicroserviceException):
    error: str = "maximum_networks_reached"


class InvalidNameError(MicroserviceException):
    error: str = "invalid_name"


class NameAlreadyInUseError(MicroserviceException):
    error: str = "name_already_in_use"


class NoPermissionsError(MicroserviceException):
    error: str = "no_permissions"
