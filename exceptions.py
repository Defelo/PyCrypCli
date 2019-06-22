import json


class InvalidServerResponseException(Exception):
    def __init__(self, response: dict):
        super().__init__("Invalid Server Response: " + json.dumps(response))


class NoResponseTimeoutException(Exception):
    def __init__(self):
        super().__init__("No Response - Timeout")


class UnknownMicroserviceException(Exception):
    def __init__(self, ms: str):
        super().__init__("Unknown Microservice: " + ms)


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


class AlreadyOwnADeviceException(Exception):
    def __init__(self):
        super().__init__("You already own a device")


class DeviceNotFoundException(Exception):
    def __init__(self):
        super().__init__("Device not found")


class PermissionDeniedException(Exception):
    def __init__(self):
        super().__init__("Permission denied")


class FileAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("File already exists")


class FileNotFoundException(Exception):
    def __init__(self):
        super().__init__("File not found")


class SourceOrDestinationInvalidException(Exception):
    def __init__(self):
        super().__init__("Source or destination invalid")


class NotEnoughCoinsException(Exception):
    def __init__(self):
        super().__init__("Not enough coins")


class AlreadyOwnAWalletException(Exception):
    def __init__(self):
        super().__init__("You already own a wallet")


class ServiceIsNotSupportedException(Exception):
    def __init__(self):
        super().__init__("Service is not supported")


class AlreadyOwnThisServiceException(Exception):
    def __init__(self):
        super().__init__("You already own a service with this name")


class ServiceNotFoundException(Exception):
    def __init__(self):
        super().__init__("Service not found")


class AttackNotRunningException(Exception):
    def __init__(self):
        super().__init__("Attack not running")


class TargetServiceNotRunningException(Exception):
    def __init__(self):
        super().__init__("Target service is not running")


class UnknownServiceException(Exception):
    def __init__(self):
        super().__init__("Unknown service")


class ServiceCannotBeUsedException(Exception):
    def __init__(self):
        super().__init__("Service cannot be used")


class MinerDoesNotExistException(Exception):
    def __init__(self):
        super().__init__("Miner does not exist.")
