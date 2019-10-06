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


class FileNotFoundException(MicroserviceException):
    error: str = "file_not_found"


class FileAlreadyExistsException(MicroserviceException):
    error: str = "file_already_exists"


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


class AttackNotRunningException(MicroserviceException):
    error: str = "attack_not_running"
