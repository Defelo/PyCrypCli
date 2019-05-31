class InvalidServerResponseException(Exception):
    def __init__(self):
        super().__init__("Invalid Server Response")


class InvalidLoginException(Exception):
    def __init__(self):
        super().__init__("Invalid Login Credentials")
