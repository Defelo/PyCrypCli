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


class SourceWalletTransactionDebtException(Exception):
    def __init__(self):
        super().__init__("Source wallet would make debt")


class InvalidWalletException(Exception):
    def __init__(self):
        super().__init__("Invalid Wallet UUID")


class InvalidKeyException(Exception):
    def __init__(self):
        super().__init__("Invalid Wallet Key")


class AlreadyOwnAWalletException(Exception):
    def __init__(self):
        super().__init__("You already own a wallet")


class AlreadyOwnServiceException(Exception):
    def __init__(self):
        super().__init__("You already own a service with this name")
