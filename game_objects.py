class Device:
    def __init__(self, uuid: str, name: str, owner: str, power: int, powered_on: bool):
        self.uuid: str = uuid
        self.name: str = name
        self.owner: str = owner
        self.power: int = power
        self.powered_on: bool = powered_on

    @staticmethod
    def deserialize(data: dict) -> 'Device':
        return Device(
            data.get("uuid"),
            data.get("name"),
            data.get("owner"),
            data.get("power"),
            data.get("powered_on")
        )


class File:
    def __init__(self, uuid: str, device: str, filename: str, content: str):
        self.uuid: str = uuid
        self.device: str = device
        self.filename: str = filename
        self.content: str = content

    @staticmethod
    def deserialize(data: dict) -> 'File':
        return File(
            data.get("uuid"),
            data.get("device"),
            data.get("filename"),
            data.get("content")
        )
