import json


class InvalidServerResponseException(Exception):
    def __init__(self, response: dict):
        super().__init__("Invalid Server Response: " + json.dumps(response))


class InvalidSessionTokenException(Exception):
    def __init__(self):
        super().__init__("Invalid session token")


class WeakPasswordException(Exception):
    def __init__(self):
        super().__init__("Password is too weak")


class UsernameAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("Username already exists")


class InvalidEmailException(Exception):
    def __init__(self):
        super().__init__("Invalid Email")


class InvalidLoginException(Exception):
    def __init__(self):
        super().__init__("Invalid Login Credentials")


class PermissionsDeniedException(Exception):
    def __init__(self):
        super().__init__("Permissions Denied")


class InvalidWalletFile(Exception):
    def __init__(self):
        super().__init__("Invalid wallet file")


class UnknownMicroserviceException(Exception):
    def __init__(self, ms: str):
        super().__init__("Unknown Microservice: " + ms)


class MicroserviceException(Exception):
    error: str = None

    def __init__(self):
        super().__init__(self.error)


class InternalErrorException(MicroserviceException):
    error: str = "internal error"


class NoResponseTimeoutException(MicroserviceException):
    error: str = "no response - timeout"


class InvalidRequestException(MicroserviceException):
    error: str = "invalid_request"


class AlreadyOwnADeviceException(MicroserviceException):
    error: str = "already_own_a_device"


class PermissionDeniedException(MicroserviceException):
    error: str = "permission_denied"


class DeviceNotFoundException(MicroserviceException):
    error: str = "device_not_found"


class IncompatibleCPUSocket(MicroserviceException):
    error: str = "incompatible_cpu_socket"


class NotEnoughRAMSlots(MicroserviceException):
    error: str = "not_enough_ram_slots"


class IncompatibleRAMTypes(MicroserviceException):
    error: str = "incompatible_ram_types"


class IncompatibleDriverInterface(MicroserviceException):
    error: str = "incompatible_drive_interface"


class FileNotFoundException(MicroserviceException):
    error: str = "file_not_found"


class FileNotChangeableException(MicroserviceException):
    error: str = "file_not_changeable"


class FileAlreadyExistsException(MicroserviceException):
    error: str = "file_already_exists"


class ParentDirectoryNotFound(MicroserviceException):
    error: str = "parent_directory_not_found"


class CanNotMoveDirIntoItselfException(MicroserviceException):
    error: str = "can_not_move_dir_into_itself"


class DirectoriesCanNotBeUpdatedException(MicroserviceException):
    error: str = "directories_can_not_be_updated"


class DirectoryCanNotHaveTextContentException(MicroserviceException):
    error: str = "directory_can_not_have_textcontent"


class AlreadyOwnAWalletException(MicroserviceException):
    error: str = "already_own_a_wallet"


class UnknownSourceOrDestinationException(MicroserviceException):
    error: str = "unknown_source_or_destination"


class NotEnoughCoinsException(MicroserviceException):
    error: str = "not_enough_coins"


class AlreadyOwnThisServiceException(MicroserviceException):
    error: str = "already_own_this_service"


class ServiceNotSupportedException(MicroserviceException):
    error: str = "service_not_supported"


class ServiceNotRunningException(MicroserviceException):
    error: str = "service_not_running"


class CannotToggleDirectlyException(MicroserviceException):
    error: str = "cannot_toggle_directly"


class CouldNotStartService(MicroserviceException):
    error: str = "could_not_start_service"


class WalletNotFoundException(MicroserviceException):
    error: str = "wallet_not_found"


class MinerNotFoundException(MicroserviceException):
    error: str = "miner_not_found"


class ServiceNotFoundException(MicroserviceException):
    error: str = "service_not_found"


class UnknownServiceException(MicroserviceException):
    error: str = "unknown_service"


class ServiceCannotBeUsedException(MicroserviceException):
    error: str = "service_cannot_be_used"


class CannotDeleteEnforcedServiceException(MicroserviceException):
    error: str = "cannot_delete_enforced_service"


class AttackNotRunningException(MicroserviceException):
    error: str = "attack_not_running"


class ItemNotFoundException(MicroserviceException):
    error: str = "item_not_found"


class CannotTradeWithYourselfException(MicroserviceException):
    error: str = "cannot_trade_with_yourself"


class UserUUIDDoesNotExistException(MicroserviceException):
    error: str = "user_uuid_does_not_exist"


class NetworkNotFoundException(MicroserviceException):
    error: str = "network_not_found"


class AlreadyMemberOfNetworkException(MicroserviceException):
    error: str = "already_member_of_network"


class InvitationAlreadyExistsException(MicroserviceException):
    error: str = "invitation_already_exists"


class CannotLeaveOwnNetworkException(MicroserviceException):
    error: str = "cannot_leave_own_network"


class CannotKickOwnerException(MicroserviceException):
    error: str = "cannot_kick_owner"


class MaximumNetworksReachedException(MicroserviceException):
    error: str = "maximum_networks_reached"


class InvalidNameException(MicroserviceException):
    error: str = "invalid_name"


class NameAlreadyInUseException(MicroserviceException):
    error: str = "name_already_in_use"


class NoPermissionsException(MicroserviceException):
    error: str = "no_permissions"
