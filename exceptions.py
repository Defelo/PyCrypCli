import json


class InvalidServerResponseException(Exception):
    def __init__(self, response: dict):
        super().__init__("Invalid Server Response: " + json.dumps(response))


class InvalidLoginException(Exception):
    def __init__(self):
        super().__init__("Invalid Login Credentials")
