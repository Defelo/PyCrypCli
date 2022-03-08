from .model import Model


class DeviceHardware(Model):
    uuid: str
    device_uuid: str
    hardware_element: str
    hardware_type: str
