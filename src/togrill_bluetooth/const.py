"""Constants"""

from dataclasses import dataclass
from typing import ClassVar

from togrill_bluetooth.services import NotifyCharacteristic, WriteCharacteristic

from .services import Service


class MainService(Service):
    uuid = "0000cee0-0000-1000-8000-00805f9b34fb"
    write = WriteCharacteristic()
    notify = NotifyCharacteristic()


@dataclass
class ManufacturerData:
    company: ClassVar[int] = 0x879A

    @staticmethod
    def decode(data: bytes):
        return ManufacturerData()
