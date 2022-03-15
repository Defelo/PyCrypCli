import json
from typing import Any, ClassVar


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
    error: ClassVar[str | None]

    def __init__(self, args: list[Any] | None = None):
        super().__init__(self.error)
        self.params = args


class InternalError(MicroserviceException):
    error = "internal error"


class NoResponseTimeoutError(MicroserviceException):
    error = "no response - timeout"


class InvalidRequestError(MicroserviceException):
    error = "invalid_request"


class AlreadyOwnADeviceError(MicroserviceException):
    error = "already_own_a_device"


class PermissionDeniedError(MicroserviceException):
    error = "permission_denied"


class DeviceNotFoundError(MicroserviceException):
    error = "device_not_found"


class DevicePoweredOffError(MicroserviceException):
    error = "device_powered_off"


class DeviceNotOnlineError(MicroserviceException):
    error = "device_not_online"


class DeviceIsStarterDeviceError(MicroserviceException):
    error = "device_is_starter_device"


class MaximumDevicesReachedError(MicroserviceException):
    error = "maximum_devices_reached"


class ElementPartNotFoundError(MicroserviceException):
    error = "element_(.+)_not_found"


class PartNotInInventoryError(MicroserviceException):
    error = "(.+)_not_in_inventory"


class MissingPartError(MicroserviceException):
    error = "missing_(.+)"


class IncompatibleCPUSocketError(MicroserviceException):
    error = "incompatible_cpu_socket"


class NotEnoughRAMSlotsError(MicroserviceException):
    error = "not_enough_ram_slots"


class IncompatibleRAMTypesError(MicroserviceException):
    error = "incompatible_ram_types"


class IncompatibleDriverInterfaceError(MicroserviceException):
    error = "incompatible_drive_interface"


class FileNotFoundError(MicroserviceException):
    error = "file_not_found"


class FileNotChangeableError(MicroserviceException):
    error = "file_not_changeable"


class FileAlreadyExistsError(MicroserviceException):
    error = "file_already_exists"


class ParentDirectoryNotFoundError(MicroserviceException):
    error = "parent_directory_not_found"


class CanNotMoveDirIntoItselfError(MicroserviceException):
    error = "can_not_move_dir_into_itself"


class DirectoriesCanNotBeUpdatedError(MicroserviceException):
    error = "directories_can_not_be_updated"


class DirectoryCanNotHaveTextContentError(MicroserviceException):
    error = "directory_can_not_have_textcontent"


class AlreadyOwnAWalletError(MicroserviceException):
    error = "already_own_a_wallet"


class UnknownSourceOrDestinationError(MicroserviceException):
    error = "unknown_source_or_destination"


class NotEnoughCoinsError(MicroserviceException):
    error = "not_enough_coins"


class AlreadyOwnThisServiceError(MicroserviceException):
    error = "already_own_this_service"


class ServiceNotSupportedError(MicroserviceException):
    error = "service_not_supported"


class ServiceNotRunningError(MicroserviceException):
    error = "service_not_running"


class CannotToggleDirectlyError(MicroserviceException):
    error = "cannot_toggle_directly"


class CouldNotStartServiceError(MicroserviceException):
    error = "could_not_start_service"


class WalletNotFoundError(MicroserviceException):
    error = "wallet_not_found"


class MinerNotFoundError(MicroserviceException):
    error = "miner_not_found"


class ServiceNotFoundError(MicroserviceException):
    error = "service_not_found"


class UnknownServiceError(MicroserviceException):
    error = "unknown_service"


class ServiceCannotBeUsedError(MicroserviceException):
    error = "service_cannot_be_used"


class CannotDeleteEnforcedServiceError(MicroserviceException):
    error = "cannot_delete_enforced_service"


class AttackNotRunningError(MicroserviceException):
    error = "attack_not_running"


class ItemNotFoundError(MicroserviceException):
    error = "item_not_found"


class CannotTradeWithYourselfError(MicroserviceException):
    error = "cannot_trade_with_yourself"


class UserUUIDDoesNotExistError(MicroserviceException):
    error = "user_uuid_does_not_exist"


class NetworkNotFoundError(MicroserviceException):
    error = "network_not_found"


class AlreadyMemberOfNetworkError(MicroserviceException):
    error = "already_member_of_network"


class InvitationAlreadyExistsError(MicroserviceException):
    error = "invitation_already_exists"


class CannotLeaveOwnNetworkError(MicroserviceException):
    error = "cannot_leave_own_network"


class CannotKickOwnerError(MicroserviceException):
    error = "cannot_kick_owner"


class MaximumNetworksReachedError(MicroserviceException):
    error = "maximum_networks_reached"


class InvalidNameError(MicroserviceException):
    error = "invalid_name"


class NameAlreadyInUseError(MicroserviceException):
    error = "name_already_in_use"


class NoPermissionsError(MicroserviceException):
    error = "no_permissions"
